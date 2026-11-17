"""
AdVision AI — build the validated creative dataset from live-card evidence.

Inputs (read-only):
  data/legacy/all_brands_ads.csv           legacy 50-record dataset (immutable)
  data/quality/live_cards.json                live-card evidence for the 50 legacy IDs
  data/quality/replacement_cards.json         live-card evidence for replacement candidates
  data/quality/replacement_candidates.json    candidate pool, best-first per brand
  data/quality/visual_review.json             recorded human/orchestrator visual decisions

Outputs:
  data/quality/advertiser_verification.csv    workstream 1: legacy vs live, per legacy ID
  data/creatives/verified/<slug>/<ad_id>.<ext> workstream 2: verified assets (byte copies)
  data/quality/recovery_manifest.csv          workstream 2: source URL, method, dims, hash, time
  data/quality/image_quality_report.csv       workstream 4
  data/quality/duplicate_groups.json          workstream 4
  reports/creative_contact_sheets/*.png       workstream 4
  data/processed/validated_dataset.{csv,json} workstream 5
  data/quality/replacement_mapping.csv        workstream 5
  data/quality/dataset_integrity_report.json  workstream 5

Acceptance (final_status = VERIFIED only if all hold):
  advertiser_verification_status == VERIFIED   live card advertiser belongs to the brand
  image_verification_status      == VERIFIED   asset downloaded from that exact card
  metadata_verification_status   == VERIFIED   metadata taken from that same card; start date present
  image_quality_status           == PASS       objective thresholds + recorded visual review "pass"
  duplicate_status               in {UNIQUE, GROUP_REPRESENTATIVE}
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from config.settings import BRAND_ALIASES, OFFICIAL_ADVERTISERS, TARGET_BRANDS  # noqa: E402
from src.quality import contact_sheet, hamming, metrics  # noqa: E402

Q = ROOT / "data" / "quality"
VERIFIED_DIR = ROOT / "data" / "creatives" / "verified"
SHEETS = ROOT / "reports" / "creative_contact_sheets"
LEGACY_CSV = ROOT / "data" / "legacy" / "all_brands_ads.csv"
TARGET_PER_BRAND = 10

# Objective quality thresholds (documented in reports/creative_quality_audit.md)
MIN_LONG_SIDE = 600        # Ad Library serves static creatives at <= 600px longest side
MIN_SHARPNESS = 100.0      # Laplacian variance at 600px short side; below = visibly soft
MIN_CONTRAST = 0.05        # luma std; below = near-blank
NEAR_DUP_HAMMING = 6       # 64-bit dHash distance

BRAND_KEYS = {b: m["slug"] for b, m in TARGET_BRANDS.items()}
BRAND_EXACT = {"kapiva", "oziva", "mamaearth", "muscleblaze", "himalaya wellness", "himalaya"}


def load(p: Path, default):
    return json.loads(p.read_text()) if p.exists() else default


def rel(p) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def advertiser_status(brand: str, advertiser: str | None, page_link: str | None = None) -> str:
    """VERIFIED (allowlisted official page or partnership naming one), NEEDS_REVIEW (look-alike
    name or page link disagrees with the allowlist), MISMATCH (another advertiser)."""
    if not advertiser:
        return "UNVERIFIED"
    official = OFFICIAL_ADVERTISERS.get(brand, {})
    if advertiser in official:
        handle = official[advertiser]
        if page_link and handle.lower() not in page_link.lower():
            return "NEEDS_REVIEW"
        return "VERIFIED"
    if " with " in advertiser and advertiser.rsplit(" with ", 1)[1].strip() in official:
        return "VERIFIED"
    if BRAND_KEYS[brand].split("_")[0] in advertiser.lower().replace(" ", ""):
        return "NEEDS_REVIEW"
    return "MISMATCH"


def advertiser_belongs(brand: str, advertiser: str | None, page_link: str | None = None) -> bool:
    return advertiser_status(brand, advertiser, page_link) == "VERIFIED"


def advertiser_type(advertiser: str) -> str:
    a = advertiser.lower().strip()
    if " with " in a:
        return "partnership"
    return "brand_page" if a in BRAND_EXACT else "sub_brand_page"


def domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        d = urlparse(url if "://" in url else "https://" + url).netloc.lower()
        return d[4:] if d.startswith("www.") else d
    except ValueError:
        return None


def norm_text(s: str | None) -> str:
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def legacy_vs_live(leg: dict, card: dict) -> dict:
    """Field-level comparison of the legacy row with the live card for the same ID."""
    def cmp(a, b):
        if not a and not b:
            return "both_empty"
        if not a or not b:
            return "missing_one"
        return "match" if a == b else "mismatch"
    leg_copy = norm_text(leg.get("ad_copy") or leg.get("link_headline"))
    live_copy = norm_text((card.get("body") or "") + " " + (card.get("link_headline") or ""))
    copy = ("both_empty" if not leg_copy and not live_copy else
            "match" if leg_copy and leg_copy[:40] in live_copy else "mismatch")
    return {
        "page_name": cmp(leg.get("page_name"), card.get("advertiser")),
        "start_date": cmp(leg.get("start_date"), card.get("start_date")),
        "cta": cmp((leg.get("cta") or "").lower(), (card.get("cta") or "").lower()),
        "landing_domain": cmp(domain(leg.get("landing_page_url")), domain(card.get("landing_url"))),
        "copy": copy,
    }


def ad_url(ad_id: str) -> str:
    return f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=IN&id={ad_id}&media_type=all"


def reparse(card: dict) -> dict:
    """Re-derive status from the stored card text with the current parser (fixes cards whose first
    line is a 'Link to ad' panel). Uses stored evidence only, so no network traffic."""
    if card.get("card_text"):
        from src.scraper.ad_library_cards import parse_card
        card = {**card, "status": parse_card(card["card_text"], [])["status"]}
    return card


def evaluate(ad_id: str, brand: str, card: dict, review: dict, origin: str) -> dict:
    """Evaluate one ad against the acceptance rules (duplicates handled later)."""
    card = reparse(card)
    r = {"ad_id": ad_id, "brand": brand, "record_origin": origin, "advertiser": card.get("advertiser"),
         "ad_library_url": ad_url(ad_id), "exclusion_reasons": []}
    ex = r["exclusion_reasons"]
    if not card.get("found"):
        r.update(advertiser_verification_status="UNVERIFIED", image_verification_status="UNVERIFIED",
                 metadata_verification_status="UNVERIFIED", image_quality_status="UNVERIFIED")
        ex.append("live card not found" + (" (login wall)" if card.get("login_wall") else ""))
        return r
    adv_status = advertiser_status(brand, card.get("advertiser"), card.get("page_link"))
    belongs = adv_status == "VERIFIED"
    r["advertiser_verification_status"] = adv_status
    r["advertiser_page_link"] = card.get("page_link")
    r["advertiser_type"] = advertiser_type(card["advertiser"]) if belongs else (
        "unconfirmed_lookalike" if adv_status == "NEEDS_REVIEW" else "other_advertiser")
    if adv_status == "MISMATCH":
        ex.append(f"advertiser is '{card.get('advertiser')}', not {brand}")
    elif adv_status == "NEEDS_REVIEW":
        ex.append(f"advertiser '{card.get('advertiser')}' resembles {brand} but is not a confirmed official page")
    for k in ("status", "start_date", "end_date", "body", "link_caption", "link_headline", "cta",
              "landing_url", "landing_url_fb_redirect", "format", "n_ads_same_creative",
              "multiple_versions", "retrieved_at", "evidence_source"):
        r[k] = card.get(k)
    r["image_type"] = card.get("asset_kind")
    has_asset = bool(card.get("asset_path")) and (ROOT / card["asset_path"]).exists()
    r["image_verification_status"] = "VERIFIED" if (belongs and has_asset) else (
        "NOT_APPLICABLE" if not belongs else "MISSING")
    if belongs and not has_asset:
        ex.append(f"creative not recoverable: {card.get('download_error') or 'no asset on card'}")
    r["metadata_verification_status"] = "VERIFIED" if (belongs and card.get("start_date")) else (
        "NOT_APPLICABLE" if not belongs else "INCOMPLETE")
    if belongs and not card.get("start_date"):
        ex.append("start date missing on card")
    if not has_asset:
        r["image_quality_status"] = "UNVERIFIED"
        return r
    m = metrics(ROOT / card["asset_path"])
    r.update(asset_path=card["asset_path"], image_source_url=card.get("asset_url"),
             retrieval_method=card.get("retrieval_method"), image_sha256=card.get("asset_sha256"),
             original_width=card.get("asset_width"), original_height=card.get("asset_height"),
             image_width=m["w"], image_height=m["h"], sharpness=m["sharpness"],
             contrast=m["contrast"], brightness=m["brightness"], dhash=m["dhash"],
             bytes_per_pixel=round(card.get("asset_bytes", 0) / (m["w"] * m["h"]), 3))
    problems = []
    if max(m["w"], m["h"]) < MIN_LONG_SIDE:
        problems.append(f"longest side {max(m['w'], m['h'])}px < {MIN_LONG_SIDE}")
    if m["sharpness"] < MIN_SHARPNESS:
        problems.append(f"sharpness {m['sharpness']} < {MIN_SHARPNESS}")
    if m["contrast"] < MIN_CONTRAST:
        problems.append(f"contrast {m['contrast']} < {MIN_CONTRAST} (near-blank)")
    decision = (review or {}).get("decision")
    if decision == "reject":
        problems.append(f"visual review: {review.get('reason')}")
    if problems:
        r["image_quality_status"] = "VIDEO_ONLY" if (r["image_type"] == "video_thumbnail" and decision == "reject") else "REPLACE"
        ex.extend(problems)
    elif decision != "pass":
        r["image_quality_status"] = "NEEDS_REVIEW"
        ex.append("no recorded visual review")
    else:
        r["image_quality_status"] = "PASS"
    r["visual_review"] = (review or {}).get("reason")
    return r


def duplicate_groups(records: list) -> list:
    """Union-find over exact sha256 matches and dHash near-duplicates."""
    recs = [r for r in records if r.get("dhash")]
    parent = {r["ad_id"]: r["ad_id"] for r in recs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    edges = []
    for i, a in enumerate(recs):
        for b in recs[i + 1:]:
            exact = a["image_sha256"] == b["image_sha256"]
            d = hamming(a["dhash"], b["dhash"])
            if exact or d <= NEAR_DUP_HAMMING:
                parent[find(a["ad_id"])] = find(b["ad_id"])
                edges.append({"a": a["ad_id"], "b": b["ad_id"], "exact_sha256": exact, "dhash_distance": d})
    groups = defaultdict(list)
    for r in recs:
        groups[find(r["ad_id"])].append(r["ad_id"])
    out = []
    for members in groups.values():
        if len(members) > 1:
            es = [e for e in edges if e["a"] in members and e["b"] in members]
            out.append({"members": sorted(members), "edges": es,
                        "kind": "exact" if all(e["exact_sha256"] for e in es) else "near"})
    return out


def main():
    legacy = list(csv.DictReader(open(LEGACY_CSV, encoding="utf-8")))
    live = load(Q / "live_cards.json", {})
    repl_cards = load(Q / "replacement_cards.json", {})
    # Dedicated MuscleBlaze full recapture (fresh evidence) supersedes earlier captures for those IDs.
    mb_recapture = load(Q / "muscleblaze_recapture_cards.json", {})
    for k, v in mb_recapture.items():
        v = {**v, "evidence_source": "muscleblaze_recapture_cards.json"}
        if k in live:
            live[k] = v
        else:
            repl_cards[k] = v
    cands = load(Q / "replacement_candidates.json", {}).get("candidates", {})
    for brand, lst in load(Q / "replacement_candidates_lead.json", {}).get("candidates", {}).items():
        have = {c["ad_id"] for c in cands.get(brand, [])}
        cands.setdefault(brand, []).extend(c for c in lst if c["ad_id"] not in have)
    vr = load(Q / "visual_review.json", {})
    reviews, dup_decisions = vr.get("reviews", {}), vr.get("duplicate_decisions", {})
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    # ---- workstream 1: advertiser verification of legacy IDs
    av_rows = []
    originals = []
    for leg in legacy:
        card = live.get(leg["ad_id"], {"found": False})
        canonical = BRAND_ALIASES[leg["brand"]]
        r = evaluate(leg["ad_id"], canonical, card, reviews.get(leg["ad_id"]), "original")
        r["legacy_brand_label"] = leg["brand"]
        cmp = legacy_vs_live(leg, card) if card.get("found") else {}
        r.update(legacy_page_name=leg["page_name"], legacy_local_image_path="data/legacy/" + leg["local_image_path"],
                 legacy_ad_copy=leg.get("ad_copy") or leg.get("link_headline"),
                 legacy_cta=leg["cta"], legacy_start_date=leg["start_date"],
                 legacy_landing_page_url=leg["landing_page_url"],
                 legacy_image_quality_status=leg.get("image_quality_status"),
                 legacy_original_ad_id=leg.get("original_ad_id"),
                 legacy_metadata_consistent=all(v in ("match", "both_empty") for v in cmp.values()) if cmp else None)
        originals.append(r)
        av_rows.append({"ad_id": leg["ad_id"], "dataset_brand": canonical, "legacy_brand_label": leg["brand"],
                        "legacy_page_name": leg["page_name"],
                        "live_card_found": card.get("found", False), "live_advertiser": card.get("advertiser"),
                        "live_page_link": card.get("page_link"),
                        "advertiser_verification_status": r["advertiser_verification_status"],
                        "advertiser_type": r.get("advertiser_type"), "live_status": card.get("status"),
                        "live_dates": card.get("dates"), "live_format": card.get("format"),
                        "live_cta": card.get("cta"), "live_landing_url": card.get("landing_url"),
                        **{f"legacy_vs_live_{k}": v for k, v in cmp.items()},
                        "n_ads_same_creative": card.get("n_ads_same_creative"),
                        "retrieved_at": card.get("retrieved_at"), "evidence": "data/quality/live_cards.json"})
    write_csv(Q / "advertiser_verification.csv", av_rows)

    # ---- replacement candidates (evaluated the same way)
    replacements = []
    for brand_raw, lst in cands.items():
        brand = BRAND_ALIASES.get(brand_raw, brand_raw)
        for rank, c in enumerate(lst):
            if c.get("visual_check") == "reject":
                continue
            card = repl_cards.get(c["ad_id"], {"found": False})
            rv = reviews.get(c["ad_id"])
            r = evaluate(c["ad_id"], brand, card, rv, "replacement")
            r["candidate_rank"] = rank
            r["legacy_brand_label"] = None
            replacements.append(r)

    orig_ids = {r["ad_id"] for r in originals}
    seen, uniq = set(), []
    for r in replacements:
        if r["ad_id"] not in orig_ids and r["ad_id"] not in seen:
            seen.add(r["ad_id"])
            uniq.append(r)
    replacements = uniq
    pool = originals + replacements

    # ---- workstream 4: duplicates (group decisions are recorded, not silent)
    groups = duplicate_groups([r for r in pool if r.get("image_verification_status") == "VERIFIED"])
    by_id = {r["ad_id"]: r for r in pool}
    for r in pool:
        r["duplicate_status"] = "UNIQUE" if r.get("dhash") else "NOT_CHECKED"
        r["duplicate_group"] = None
    for gi, g in enumerate(groups):
        gid = f"dup{gi + 1:02d}"
        g["group_id"] = gid
        dec = dup_decisions.get(gid) or next((d for d in dup_decisions.values()
                                              if set(d.get("members", [])) == set(g["members"])), None)
        # default representative: best eligible original, then best candidate, by sharpness
        def key(a):
            x = by_id[a]
            return (x["record_origin"] != "original", x.get("image_quality_status") != "PASS", -x.get("sharpness", 0))
        rep = (dec or {}).get("keep") or sorted(g["members"], key=key)[0]
        keep_all = (dec or {}).get("keep_all", False)
        g.update(representative=rep, decision=(dec or {}).get("reason", "auto: best original by quality"),
                 keep_all=keep_all, brands=sorted({by_id[m]["brand"] for m in g["members"]}))
        for m in g["members"]:
            by_id[m]["duplicate_group"] = gid
            if keep_all:
                by_id[m]["duplicate_status"] = "NEAR_DUPLICATE_KEPT"
            elif m == rep:
                by_id[m]["duplicate_status"] = "GROUP_REPRESENTATIVE"
            else:
                by_id[m]["duplicate_status"] = f"DUPLICATE_OF:{rep}"
                by_id[m]["exclusion_reasons"].append(f"duplicate creative of {rep} ({gid})")

    def eligible(r):
        return (r.get("advertiser_verification_status") == "VERIFIED"
                and r.get("image_verification_status") == "VERIFIED"
                and r.get("metadata_verification_status") == "VERIFIED"
                and r.get("image_quality_status") == "PASS"
                and r.get("duplicate_status") in ("UNIQUE", "GROUP_REPRESENTATIVE", "NEAR_DUPLICATE_KEPT"))

    # ---- workstream 5: selection, replacement mapping
    final, mapping = [], []
    for brand in TARGET_BRANDS:
        orig_b = [r for r in originals if r["brand"] == brand]
        keep = [r for r in orig_b if eligible(r)]
        failed = [r for r in orig_b if not eligible(r)]
        repl_b = sorted([r for r in replacements if r["brand"] == brand and eligible(r)],
                        key=lambda r: r["candidate_rank"])
        chosen_sha = {r["image_sha256"] for r in keep}
        for f in failed:
            new = None
            while repl_b and len(keep) < TARGET_PER_BRAND:
                c = repl_b.pop(0)
                if c["image_sha256"] in chosen_sha:
                    continue
                new = c
                break
            f["replacement_status"] = "replaced" if new else "unavailable_for_visual_analysis"
            f["replacement_reason"] = "; ".join(f["exclusion_reasons"])
            f["replaced_by_ad_id"] = new["ad_id"] if new else None
            if new:
                new.update(replacement_status="replacement", replaces_ad_id=f["ad_id"],
                           replacement_reason=f["replacement_reason"])
                keep.append(new)
                chosen_sha.add(new["image_sha256"])
            mapping.append({"brand": brand, "original_ad_id": f["ad_id"],
                            "original_advertiser": f.get("advertiser"),
                            "failure_reason": f["replacement_reason"],
                            "replacement_ad_id": new["ad_id"] if new else None,
                            "replacement_advertiser": new["advertiser"] if new else None,
                            "status": f["replacement_status"]})
        for r in orig_b:
            if eligible(r):
                r["replacement_status"] = "retained"
        final.extend(keep)

    for r in pool:
        r["final_status"] = "VERIFIED" if (eligible(r) and r in final) else "EXCLUDED"
        if r["final_status"] == "EXCLUDED" and r["record_origin"] == "replacement" and eligible(r):
            r["exclusion_reasons"].append("eligible spare candidate (brand target already met)")

    # ---- workstream 2: copy verified assets (byte-identical) + manifest
    manifest = []
    for r in pool:
        if r.get("image_verification_status") != "VERIFIED":
            continue
        src = ROOT / r["asset_path"]
        dst = VERIFIED_DIR / BRAND_KEYS[r["brand"]] / f"{r['ad_id']}{src.suffix}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copy2(src, dst)
        r["local_image_path"] = rel(dst)
        manifest.append({"ad_id": r["ad_id"], "brand": r["brand"], "record_origin": r["record_origin"],
                         "local_image_path": r["local_image_path"], "source_url": r["image_source_url"],
                         "retrieval_method": r["retrieval_method"], "image_type": r["image_type"],
                         "original_dimensions": f"{r['original_width']}x{r['original_height']}",
                         "final_dimensions": f"{r['image_width']}x{r['image_height']}",
                         "resized": False, "verification_status": r["image_verification_status"],
                         "retrieved_at": r["retrieved_at"], "sha256": r["image_sha256"],
                         "evidence_source": r.get("evidence_source") or ("live_cards.json" if r["record_origin"] == "original" else "replacement_cards.json")})
    write_csv(Q / "recovery_manifest.csv", manifest)

    # ---- quality report + duplicate groups + contact sheets
    qcols = ["ad_id", "brand", "record_origin", "image_type", "image_width", "image_height", "sharpness",
             "contrast", "brightness", "bytes_per_pixel", "image_sha256", "dhash", "image_quality_status",
             "visual_review", "duplicate_status", "duplicate_group", "final_status"]
    write_csv(Q / "image_quality_report.csv", [{k: r.get(k) for k in qcols} for r in pool if r.get("dhash")])
    (Q / "duplicate_groups.json").write_text(json.dumps(
        {"generated_at": now, "method": {"exact": "sha256 of downloaded bytes",
                                         "near": f"64-bit dHash hamming <= {NEAR_DUP_HAMMING}"},
         "groups": groups}, indent=1))
    SHEETS.mkdir(parents=True, exist_ok=True)
    for brand, slug in BRAND_KEYS.items():
        for label, sel in (("accepted", lambda r: r["final_status"] == "VERIFIED"),
                           ("rejected", lambda r: r["final_status"] != "VERIFIED" and r.get("local_image_path"))):
            rs = [r for r in pool if r["brand"] == brand and sel(r)]
            if rs:
                contact_sheet([ROOT / r["local_image_path"] for r in rs],
                              [f"{r['ad_id']} {r.get('image_quality_status')}/{r.get('duplicate_status', '')[:12]}"
                               for r in rs], SHEETS / f"{slug}_{label}.png", cols=5, t=240)

    # ---- validated dataset
    cols = ["ad_id", "brand", "legacy_brand_label", "advertiser", "advertiser_type", "advertiser_page_link",
            "record_origin", "final_status",
            "advertiser_verification_status", "image_verification_status", "metadata_verification_status",
            "image_quality_status", "duplicate_status", "duplicate_group", "exclusion_reasons",
            "replacement_status", "replaces_ad_id", "replaced_by_ad_id", "replacement_reason",
            "ad_library_url", "status", "start_date", "end_date", "body", "link_caption", "link_headline",
            "cta", "landing_url", "landing_url_fb_redirect", "format", "image_type", "n_ads_same_creative",
            "multiple_versions", "local_image_path", "image_source_url", "retrieval_method", "retrieved_at", "evidence_source",
            "image_sha256", "original_width", "original_height", "image_width", "image_height",
            "sharpness", "contrast", "brightness", "visual_review", "legacy_page_name",
            "legacy_local_image_path", "legacy_ad_copy", "legacy_cta", "legacy_start_date",
            "legacy_landing_page_url", "legacy_image_quality_status", "legacy_original_ad_id",
            "legacy_metadata_consistent"]
    out_rows = [r for r in pool if r["record_origin"] == "original" or r["final_status"] == "VERIFIED"]
    out_rows.sort(key=lambda r: (list(TARGET_BRANDS).index(r["brand"]), r["final_status"] != "VERIFIED",
                                 r["record_origin"] != "original", r["ad_id"]))
    flat = [{c: ("; ".join(r[c]) if c == "exclusion_reasons" else r.get(c)) for c in cols} for r in out_rows]
    write_csv(ROOT / "data/processed/validated_dataset.csv", flat, cols)
    counts = {b: sum(1 for r in final if r["brand"] == b) for b in TARGET_BRANDS}
    (ROOT / "data/processed/validated_dataset.json").write_text(json.dumps(
        {"meta": {"generated_at": now, "source": "live Ad Library cards (see data/quality/*)",
                  "n_rows": len(flat), "n_verified": len(final), "verified_per_brand": counts,
                  "acceptance_rules": __doc__.split("Acceptance")[1].strip(),
                  "legacy_dataset": rel(LEGACY_CSV)}, "ads": flat}, indent=1, ensure_ascii=False))
    write_csv(Q / "replacement_mapping.csv", mapping)

    # ---- integrity checks
    integrity = integrity_checks(flat, final)
    (Q / "dataset_integrity_report.json").write_text(json.dumps(integrity, indent=1))
    print(json.dumps({"verified_per_brand": counts, "n_verified": len(final),
                      "dup_groups": len(groups), "integrity_passed": integrity["passed"]}, indent=1))
    return 0 if integrity["passed"] else 1


def integrity_checks(rows: list, final: list) -> dict:
    ver = [r for r in rows if r["final_status"] == "VERIFIED"]
    checks = []

    def check(name, ok, detail=None):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    ids = [r["ad_id"] for r in rows]
    check("unique ad_id across dataset", len(ids) == len(set(ids)),
          [i for i in set(ids) if ids.count(i) > 1])
    paths = [r["local_image_path"] for r in ver]
    check("unique image path per verified ad", len(paths) == len(set(paths)))
    shas = [r["image_sha256"] for r in ver]
    check("no identical image bytes across verified ads", len(shas) == len(set(shas)))
    bad_file = []
    import hashlib
    for r in ver:
        p = ROOT / (r["local_image_path"] or "")
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != r["image_sha256"]:
            bad_file.append(r["ad_id"])
    check("verified image exists and sha256 matches", not bad_file, bad_file)
    check("verified ads: advertiser is an allowlisted official page or partnership",
          all(advertiser_belongs(r["brand"], r["advertiser"], r.get("advertiser_page_link")) for r in ver))
    check("brand names are canonical", all(r["brand"] in TARGET_BRANDS for r in rows),
          sorted({r["brand"] for r in rows} - set(TARGET_BRANDS)))
    check("verified ads: all five status fields pass", all(
        r["advertiser_verification_status"] == "VERIFIED" and r["image_verification_status"] == "VERIFIED"
        and r["metadata_verification_status"] == "VERIFIED" and r["image_quality_status"] == "PASS"
        for r in ver))
    check("verified ads: start_date parses", all(
        _parses(r["start_date"]) for r in ver), [r["ad_id"] for r in ver if not _parses(r["start_date"])])
    bad_url = [r["ad_id"] for r in ver if r["landing_url"] and not urlparse(r["landing_url"]).scheme.startswith("http")]
    check("landing URLs are http(s) when present", not bad_url, bad_url)
    check("verified count matches selection", len(ver) == len(final))
    missing = {f: sum(1 for r in ver if not r.get(f)) for f in ("cta", "landing_url", "body", "end_date")}
    return {"passed": all(c["passed"] for c in checks), "checks": checks,
            "verified_records_missing_optional_fields": missing,
            "note": "Missing optional fields are left empty (unavailable on the live card), never inferred."}


def _parses(d):
    try:
        time.strptime(d, "%d %b %Y")
        return True
    except (TypeError, ValueError):
        return False


def write_csv(p: Path, rows: list, cols: list | None = None):
    p.parent.mkdir(parents=True, exist_ok=True)
    cols = cols or (list(rows[0].keys()) if rows else [])
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())

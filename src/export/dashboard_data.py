"""
Export analysis outputs for the dashboard (docs/dashboard_data_contract.md).

    python -m src.export.dashboard_data [--variant clip] [--out dashboard/public/data]

Rules enforced here (the dashboard never computes or invents values):
  * Only final_status == VERIFIED rows are exported as ads.
  * provisional = True unless the freeze marker matches the dataset sha256. A frozen dataset
    reads pipeline outputs from <outputs.root>; an unfrozen one only from <outputs.root>/provisional.
  * Feature / cluster / insight sections are exported only when their pipeline outputs exist AND
    cover exactly the exported ad IDs; otherwise `available.*` is false and the section is null.
  * Images are byte copies of the verified assets.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import TARGET_BRANDS  # noqa: E402

log = logging.getLogger("advision.export")
SCHEMA_VERSION = "1.0"
FEATURE_KEYS = ["width", "height", "aspect_ratio", "orientation", "brightness", "contrast", "sharpness",
                "colourfulness", "dominant_colours", "colour_distribution", "text_density", "text_position",
                "ocr_text", "layout_category", "layout_reasons"]


class ExportError(RuntimeError):
    pass


def _none(v):
    return None if v in ("", None) else v


def _float(v):
    try:
        return None if v in ("", None) else float(v)
    except ValueError:
        return None


def normalise_cta(cta: Optional[str]) -> Optional[str]:
    return " ".join(cta.split()).title() if cta else None


def _status(s: Optional[str]) -> Optional[str]:
    return s if s in ("Active", "Inactive") else None


def load_config(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def export(config_path: Path, out_dir: Path, variant: str = "clip") -> dict:
    cfg = load_config(config_path)
    inp = {k: (ROOT / v if isinstance(v, str) and not Path(v).is_absolute() else v) for k, v in cfg["inputs"].items()}
    ds_path = Path(inp["dataset_csv"])
    if not ds_path.is_file():
        raise ExportError(f"dataset not found: {ds_path}")
    rows = list(csv.DictReader(open(ds_path, encoding="utf-8")))
    ver = [r for r in rows if r.get("final_status") == "VERIFIED"]
    if not ver:
        raise ExportError("no VERIFIED rows to export")
    ds_sha = hashlib.sha256(ds_path.read_bytes()).hexdigest()
    marker_p = Path(inp["freeze_marker"])
    marker = json.loads(marker_p.read_text()) if marker_p.is_file() else {}
    frozen = marker.get("dataset_sha256") == ds_sha
    out_root = Path(cfg["outputs"]["root"])
    out_root = out_root if out_root.is_absolute() else ROOT / out_root
    run_dir = out_root if frozen else out_root / "provisional"
    ids = [r["ad_id"] for r in ver]

    # ---- features (only if they cover exactly the exported ids)
    features: Dict[str, dict] = {}
    fj = Path(inp["features_json"])
    clip_model = None
    if fj.is_file():
        fdata = json.loads(fj.read_text())
        recs = {r["ad_id"]: r for r in fdata.get("records", [])}
        f_sha = fdata.get("meta", {}).get("selection", {}).get("dataset_sha256")
        if f_sha != ds_sha:
            log.warning("visual_features.json was built from a different dataset version (%s != %s); "
                        "features not exported", str(f_sha)[:12], ds_sha[:12])
        elif set(recs) == set(ids):
            features = {a: {k: recs[a].get(k) for k in FEATURE_KEYS} for a in ids
                        if recs[a].get("extraction_status") in ("success", "partial")}
            clip_model = fdata.get("meta", {}).get("clip", {}).get("model")
        else:
            log.warning("visual_features.json covers %d ads but %d are VERIFIED; features not exported",
                        len(recs), len(ids))

    # ---- clustering / analytics / intelligence (from the matching run directory)
    cdir, adir, idir = run_dir / "clustering" / variant, run_dir / "analytics" / variant, run_dir / "intelligence" / variant
    assignments: Dict[str, dict] = {}
    run_manifest = run_dir / "run_manifest.json"
    rm = json.loads(run_manifest.read_text()) if run_manifest.is_file() else None
    run_sha = ((rm or {}).get("summary", {}).get("dataset") or {}).get("sha256")
    run_fresh = run_sha == ds_sha
    if rm is not None and not run_fresh:
        log.warning("pipeline run used a different dataset version (%s != %s); clusters/insights not exported",
                    str(run_sha)[:12], ds_sha[:12])
    if run_fresh and (cdir / "assignments.csv").is_file():
        arows = list(csv.DictReader(open(cdir / "assignments.csv", encoding="utf-8")))
        if {r["ad_id"] for r in arows} == set(ids):
            assignments = {r["ad_id"]: r for r in arows}
        else:
            log.warning("assignments do not cover exactly the VERIFIED ads; clusters not exported")
    clusters_file = None
    if assignments and (cdir / "selected_configuration.json").is_file():
        clusters_file = _clusters(cdir, adir, idir, assignments, {r["ad_id"]: r["brand"] for r in ver})

    insights = None
    if assignments and (idir / "observations.json").is_file():
        obs = json.loads((idir / "observations.json").read_text()).get("observations", [])
        bad = [o["observation_id"] for o in obs if not set(o.get("supporting_ad_ids", [])) <= set(ids)]
        if bad:
            raise ExportError(f"observations reference ads that are not exported: {bad[:5]}")
        insights = [{k: o.get(k) for k in ("observation_id", "scope", "statement", "metric", "value", "comparison",
                                            "n", "supporting_ad_ids", "method", "caveats", "status")} for o in obs]

    # ---- ads + images
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        prev = out_dir / "manifest.json"
        is_export = prev.is_file() and json.loads(prev.read_text()).get("schema_version") == SCHEMA_VERSION
        if not is_export:
            raise ExportError(f"refusing to overwrite {out_dir}: not empty and not a previous dashboard export")
        shutil.rmtree(out_dir)  # a previous export: always rebuilt from scratch
    (out_dir / "creatives").mkdir(parents=True)
    ads: List[dict] = []
    for r in ver:
        src = ROOT / r["local_image_path"]
        if not src.is_file():
            raise ExportError(f"{r['ad_id']}: verified image missing at {src}")
        slug = TARGET_BRANDS[r["brand"]]["slug"]
        dst = out_dir / "creatives" / slug / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        a = assignments.get(r["ad_id"])
        ads.append({
            "ad_id": r["ad_id"], "brand": r["brand"], "advertiser": r["advertiser"],
            "advertiser_type": r["advertiser_type"], "ad_library_url": r["ad_library_url"],
            "status": _status(r.get("status")), "start_date": _none(r.get("start_date")),
            "end_date": _none(r.get("end_date")), "body": _none(r.get("body")),
            "link_caption": _none(r.get("link_caption")), "link_headline": _none(r.get("link_headline")),
            "cta": _none(r.get("cta")), "cta_normalised": normalise_cta(_none(r.get("cta"))),
            "landing_url": _none(r.get("landing_url")), "format": _none(r.get("format")),
            "image_type": _none(r.get("image_type")), "image": f"/data/creatives/{slug}/{src.name}",
            "record_origin": r["record_origin"], "replaces_ad_id": _none(r.get("replaces_ad_id")),
            "features": features.get(r["ad_id"]),
            "cluster": None if not a else {"cluster_id": int(a["cluster_id"]), "is_noise": a["is_noise"] == "True",
                                           "distance_to_centroid": _float(a.get("distance_to_centroid"))},
        })

    if not run_fresh:
        rm = None
    manifest = {
        "schema_version": SCHEMA_VERSION, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provisional": not frozen,
        "dataset": {"sha256": ds_sha, "frozen": frozen, "frozen_at": marker.get("frozen_at") if frozen else None,
                    "n_verified": len(ver), "n_excluded": len(rows) - len(ver),
                    "per_brand": {b: sum(1 for r in ver if r["brand"] == b) for b in TARGET_BRANDS}},
        "pipeline": None if not (rm or features) else {
            "run_at": (rm or {}).get("finished_at"), "feature_variant": variant if assignments else None,
            "clustering_config": (clusters_file or {}).get("selected", {}).get("config_id"),
            "clip_model": clip_model},
        "available": {"features": bool(features), "clusters": clusters_file is not None,
                      "projection": bool(clusters_file and clusters_file.get("projection")),
                      "insights": insights is not None},
        "brands": list(TARGET_BRANDS),
    }
    _write(out_dir / "manifest.json", manifest)
    _write(out_dir / "ads.json", ads)
    if clusters_file is not None:
        _write(out_dir / "clusters.json", clusters_file)
    if insights is not None:
        _write(out_dir / "insights.json", insights)
    log.info("exported %d ads to %s (provisional=%s, available=%s)", len(ads), out_dir, not frozen, manifest["available"])
    return manifest


def _clusters(cdir: Path, adir: Path, idir: Path, assignments: Dict[str, dict], brands: Dict[str, str]) -> dict:
    sel = json.loads((cdir / "selected_configuration.json").read_text())
    sc = sel["selected_config"]
    sweep = json.loads((cdir / "sweep_results.json").read_text())
    entry = next(e for e in sweep["entries"] if e["config"]["config_id"] == sc["config_id"])
    m = entry["metrics"]
    profiles = {}
    if (idir / "cluster_profiles.json").is_file():
        profiles = json.loads((idir / "cluster_profiles.json").read_text()).get("profiles", {})
    reps = {}
    if (adir / "representatives.json").is_file():
        for v in json.loads((adir / "representatives.json").read_text()).values():
            reps[int(v["cluster_id"])] = [x["ad_id"] for x in v.get("representatives", [])]
    by_cluster: Dict[int, List[str]] = {}
    for a, r in sorted(assignments.items()):
        by_cluster.setdefault(int(r["cluster_id"]), []).append(a)
    clusters = []
    for cid, members in sorted(by_cluster.items()):
        brand_mix: Dict[str, int] = {}
        for a in members:
            b = brands[a]  # from the validated dataset, never inferred
            brand_mix[b] = brand_mix.get(b, 0) + 1
        prof = profiles.get(str(cid)) or profiles.get("noise" if cid == -1 else "", {}) or {}
        clusters.append({"cluster_id": cid, "is_noise": cid == -1, "size": len(members), "ad_ids": members,
                         "representative_ad_ids": reps.get(cid) or prof.get("representative_ad_ids", []),
                         "brand_mix": brand_mix,
                         "profile": {k: v for k, v in prof.items() if k not in ("ad_ids", "representative_ad_ids")}})
    projection = None
    pca = adir / "projections" / "pca_2d.csv"
    if pca.is_file():
        pts = list(csv.DictReader(open(pca, encoding="utf-8")))
        if {p["ad_id"] for p in pts} == set(assignments):
            projection = [{"ad_id": p["ad_id"], "x": float(p["x"]), "y": float(p["y"])} for p in pts]
    return {"selected": {"config_id": sc["config_id"], "algorithm": sc["algorithm"], "params": sc.get("params", {}),
                         "rationale": sel.get("rationale", ""), "warnings": sel.get("warnings", [])},
            "metrics": {"silhouette": m.get("silhouette"), "davies_bouldin": m.get("davies_bouldin"),
                        "calinski_harabasz": m.get("calinski_harabasz"), "n_clusters": m.get("n_clusters", 0),
                        "n_noise": m.get("n_noise", 0)},
            "clusters": clusters, "projection": projection}


def _write(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=ROOT / "config/analysis_pipeline.json")
    ap.add_argument("--out", type=Path, default=ROOT / "dashboard/public/data")
    ap.add_argument("--variant", default="clip", help="feature variant whose clustering is exported")
    a = ap.parse_args(argv)
    from src.utils.logging import setup_logging
    setup_logging()
    try:
        m = export(a.config, a.out, a.variant)
    except ExportError as e:
        log.error("%s", e)
        return 2
    print(json.dumps({k: m[k] for k in ("provisional", "available")} | {"n_verified": m["dataset"]["n_verified"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

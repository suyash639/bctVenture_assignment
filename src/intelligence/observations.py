"""
Creative intelligence: turn feature records (+ optional cluster assignments and CLIP
embeddings) into explainable, traceable observations.

Every observation is produced by a template from computed numbers. Each one carries the
metric, value, comparison baseline, n, supporting ad IDs, the method used, and caveats.
Nothing here says anything about ad delivery, outcomes or intent: observations describe
how creatives *look*, not how they *did*.

Inputs are duck-typed (see docs/analysis_data_contract.md):
  bundle       object or dict with `ad_ids` (list[str]) and `records` (dict ad_id -> record).
               A record holds visual feature fields plus an optional `record["dataset"]` row
               (brand, cta, advertiser, advertiser_type, image_type, ...). Optional
               `embeddings` (n, d), row-aligned to `ad_ids`, NaN rows = missing.
  assignments  list[dict] / CSV path with ad_id, cluster_id, is_noise[, distance_to_centroid]
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

LAYOUTS = ["product_focused", "lifestyle", "testimonial", "offer_heavy", "educational", "unknown"]
HUE_FAMILIES = {
    "red_pink": ["red", "rose", "magenta"],
    "orange_yellow": ["orange", "yellow"],
    "green": ["yellow_green", "green", "green_cyan"],
    "blue_cyan": ["cyan", "azure", "blue"],
    "violet": ["violet"],
    "white": ["white"],
    "dark_grey": ["black", "grey"],
}
CHROMATIC_FAMILIES = ["red_pink", "orange_yellow", "green", "blue_cyan", "violet"]
COLOUR_KEYS = ["white", "black", "grey", "red", "orange", "yellow", "yellow_green", "green",
               "green_cyan", "cyan", "azure", "blue", "violet", "magenta", "rose"]
NUMERIC_FEATURES = ["text_density", "brightness", "contrast", "sharpness", "colourfulness", "aspect_ratio"]
OFFER_TEXT = re.compile(r"(₹|rs\.?\s?\d|inr|\d\s?%|offer|discount|mrp|coupon|cashback|price|\boff\b|\bsale\b|\bdeal\b)",
                        re.IGNORECASE)
BANNED_TERMS = ["performs", "effective", "converts", "roi", "better results"]

CAVEAT_GENERAL = "Describes creative appearance only; it says nothing about ad delivery, audience response or outcomes."
CAVEAT_LAYOUT = "Layout labels come from a rule-based heuristic (src/vision/layout_classifier.py) that has not been validated against human labels."
CAVEAT_OCR = "OCR reads Latin script and digits; Devanagari text and the ₹ glyph are often not transcribed, so text-based counts are lower bounds."
CAVEAT_SAMPLE = "Small sample (n={n}); treat as descriptive of this dataset, not of the brand's overall advertising."
CAVEAT_CLIP = "CLIP cosine similarity reflects visual-semantic resemblance as learned by the model, not a human judgement of style."
CAVEAT_COLOUR = "Colour shares are pixel proportions in 15 HSV buckets; backgrounds and product packaging both contribute."
CAVEAT_CLUSTER = "Cluster membership depends on the chosen algorithm and parameters (see data/outputs/clustering/)."


@dataclass
class IntelligenceConfig:
    min_n: int = 3                       # minimum group size for any comparative statement
    low_text_threshold: float = 0.05     # text_density below this = low-text creative
    high_text_threshold: float = 0.15    # text_density at/above this = high-text creative
    white_dominant_threshold: float = 0.40  # colour_distribution["white"] >= this = white-dominant
    low_readability_ratio: float = 0.5   # readable/detected OCR regions below this = low readability
    top_cross_brand_pairs: int = 5
    top_distinguishing_features: int = 3
    n_representatives: int = 3
    small_sample_n: int = 10             # add a small-sample caveat below this n

    def to_dict(self):
        return asdict(self)


@dataclass
class Observation:
    observation_id: str
    scope: str                    # "dataset" | "brand:<b>" | "cluster:<id>" | "cross_brand"
    statement: str
    metric: str
    value: Optional[float]
    value_format: str             # "pct" | "num" | "int" — how `value` is rendered in `statement`
    comparison: Optional[Dict[str, Any]]
    n: int
    supporting_ad_ids: List[str]
    method: str
    caveats: List[str]
    status: str = "ok"            # "ok" | "insufficient_data"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


# ----------------------------------------------------------------------------- helpers

def fmt(value: Optional[float], kind: str) -> str:
    if value is None:
        return "n/a"
    if kind == "pct":
        return f"{value * 100:.1f}%"
    if kind == "int":
        return str(int(round(value)))
    return f"{value:.3f}"


def normalise_cta(cta: Optional[str]) -> str:
    if cta is None or not str(cta).strip():
        return "No CTA"
    return " ".join(w.capitalize() for w in str(cta).split())


def _attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _field(rec: dict, name: str):
    v = rec.get(name)
    if v is None and isinstance(rec.get("dataset"), dict):
        v = rec["dataset"].get(name)
    return v


def _num(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def load_assignments(assignments: Union[None, str, Path, Sequence[dict]]) -> Dict[str, dict]:
    """Normalise assignments to {ad_id: {cluster_id:int, is_noise:bool, distance_to_centroid}}."""
    if assignments is None:
        return {}
    rows = list(csv.DictReader(open(assignments, encoding="utf-8"))) if isinstance(assignments, (str, Path)) \
        else list(assignments)
    out = {}
    for r in rows:
        cid = int(r["cluster_id"])
        noise = r.get("is_noise")
        noise = (str(noise).strip().lower() in ("true", "1", "yes")) if noise is not None else cid == -1
        out[str(r["ad_id"])] = {"cluster_id": cid, "is_noise": bool(noise or cid == -1),
                                "distance_to_centroid": _num(r.get("distance_to_centroid"))}
    return out


class _Ctx:
    """Normalised view of the inputs shared by all analyses."""

    def __init__(self, bundle, assignments, embeddings, cfg: IntelligenceConfig):
        self.cfg = cfg
        self.ad_ids = [str(a) for a in _attr(bundle, "ad_ids")]
        recs = _attr(bundle, "records")
        self.records = {str(k): v for k, v in recs.items()}
        missing = [a for a in self.ad_ids if a not in self.records]
        if missing:
            raise ValueError(f"bundle.records missing ad_ids: {missing[:5]}")
        self.brand = {a: _field(self.records[a], "brand") or "unknown" for a in self.ad_ids}
        self.brands = sorted(set(self.brand.values()))
        emb = embeddings if embeddings is not None else _attr(bundle, "embeddings")
        self.emb: Dict[str, np.ndarray] = {}
        if emb is not None:
            emb = np.asarray(emb, dtype=np.float64)
            if emb.shape[0] != len(self.ad_ids):
                raise ValueError(f"embeddings rows ({emb.shape[0]}) != len(ad_ids) ({len(self.ad_ids)})")
            for a, v in zip(self.ad_ids, emb):
                if np.all(np.isfinite(v)) and np.linalg.norm(v) > 0:
                    self.emb[a] = v / np.linalg.norm(v)
        self.assign = load_assignments(assignments)
        self.unknown_assignment_ids = sorted(set(self.assign) - set(self.ad_ids))
        self.assign = {a: v for a, v in self.assign.items() if a in self.records}

    def by_brand(self) -> Dict[str, List[str]]:
        d = defaultdict(list)
        for a in self.ad_ids:
            d[self.brand[a]].append(a)
        return {b: sorted(v) for b, v in sorted(d.items())}

    def by_cluster(self) -> Dict[str, List[str]]:
        d = defaultdict(list)
        for a in self.ad_ids:
            if a in self.assign:
                c = self.assign[a]
                d["noise" if c["is_noise"] else str(c["cluster_id"])].append(a)
        return {k: sorted(v) for k, v in sorted(d.items(), key=lambda kv: (kv[0] == "noise", _sort_key(kv[0])))}

    def caveats(self, n: int, *extra: str) -> List[str]:
        out = [CAVEAT_GENERAL, *extra]
        if n < self.cfg.small_sample_n:
            out.append(CAVEAT_SAMPLE.format(n=n))
        return out


def _sort_key(k: str):
    return (0, int(k)) if k.lstrip("-").isdigit() else (1, k)


def _family_shares(rec: dict) -> Optional[Dict[str, float]]:
    cd = rec.get("colour_distribution")
    if not isinstance(cd, dict):
        return None
    return {fam: float(sum(_num(cd.get(k)) or 0.0 for k in keys)) for fam, keys in HUE_FAMILIES.items()}


def _colour_vec(rec: dict) -> Optional[np.ndarray]:
    cd = rec.get("colour_distribution")
    if not isinstance(cd, dict):
        return None
    return np.array([_num(cd.get(k)) or 0.0 for k in COLOUR_KEYS])


def _top(counter: Counter) -> Tuple[str, int]:
    # deterministic: highest count, then alphabetical
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0]


def _obs(ctx, oid, scope, statement, metric, value, vfmt, comparison, n, ids, method, caveats, details=None,
         comparative=True):
    status = "ok"
    if comparative and n < ctx.cfg.min_n:
        status = "insufficient_data"
        statement = f"Insufficient data (n={n} < {ctx.cfg.min_n}): " + statement
    return Observation(observation_id=oid, scope=scope, statement=statement, metric=metric,
                       value=None if value is None else round(float(value), 6), value_format=vfmt,
                       comparison=comparison, n=int(n), supporting_ad_ids=sorted(ids), method=method,
                       caveats=caveats, status=status, details=details or {})


# ----------------------------------------------------------------------------- analyses

def _distribution_obs(ctx, groups: Dict[str, List[str]], scope_fn, getter, metric, label_name, method, extra_caveats,
                      id_prefix):
    """Most frequent category per group, compared with the dataset share of that category."""
    all_vals = {a: getter(a) for a in ctx.ad_ids}
    known_all = {a: v for a, v in all_vals.items() if v is not None}
    overall = Counter(known_all.values())
    out = []
    for g, ids in groups.items():
        vals = {a: all_vals[a] for a in ids if all_vals[a] is not None}
        if not vals:
            continue
        cnt = Counter(vals.values())
        top, k = _top(cnt)
        share = k / len(vals)
        base = overall[top] / len(known_all) if known_all else None
        support = [a for a, v in vals.items() if v == top]
        stmt = (f"{top} is the most frequent {label_name} for {scope_fn(g)}: {k} of {len(vals)} creatives "
                f"({fmt(share, 'pct')}), vs {fmt(base, 'pct')} across the dataset.")
        out.append(_obs(ctx, f"{id_prefix}:{g}:{top}", scope_fn(g, raw=True), stmt, metric, share, "pct",
                        {"baseline": "dataset share of the same category", "value": base},
                        len(vals), support, method, ctx.caveats(len(vals), *extra_caveats),
                        {"distribution": dict(sorted(cnt.items())), "n_missing": len(ids) - len(vals)}))
    return out


def _scope_brand(g, raw=False):
    return f"brand:{g}" if raw else g


def _scope_cluster(g, raw=False):
    return f"cluster:{g}" if raw else ("noise points" if g == "noise" else f"cluster {g}")


def analyse_layouts(ctx) -> List[Observation]:
    get = lambda a: ctx.records[a].get("layout_category")  # noqa: E731
    method = "count of layout_category per group; share = count / records with a label"
    out = _distribution_obs(ctx, ctx.by_brand(), _scope_brand, get, "layout_share", "layout label", method,
                            [CAVEAT_LAYOUT], "layout")
    if ctx.assign:
        out += _distribution_obs(ctx, ctx.by_cluster(), _scope_cluster, get, "layout_share", "layout label",
                                 method, [CAVEAT_LAYOUT, CAVEAT_CLUSTER], "layout_cluster")
    labelled = [a for a in ctx.ad_ids if ctx.records[a].get("layout_category")]
    with_reason = [a for a in labelled if ctx.records[a].get("layout_reasons")
                   and ctx.records[a].get("layout_category") != "unknown"]
    if labelled:
        share = len(with_reason) / len(labelled)
        out.append(_obs(ctx, "layout_coverage:dataset", "dataset",
                        f"{len(with_reason)} of {len(labelled)} labelled creatives ({fmt(share, 'pct')}) received a "
                        f"non-unknown layout label with recorded rule evidence.",
                        "layout_rule_coverage", share, "pct", None, len(labelled), with_reason or labelled,
                        "share of records whose layout_category != unknown and layout_reasons is non-empty",
                        ctx.caveats(len(labelled), CAVEAT_LAYOUT), comparative=False))
    return out


def analyse_cta(ctx) -> List[Observation]:
    get = lambda a: normalise_cta(_field(ctx.records[a], "cta"))  # noqa: E731
    return _distribution_obs(ctx, ctx.by_brand(), _scope_brand, get, "cta_share", "CTA (case-normalised)",
                             "case/whitespace-normalised CTA text from the live card; share per brand", [], "cta")


def analyse_text_density(ctx) -> List[Observation]:
    cfg = ctx.cfg
    dens = {a: _num(ctx.records[a].get("text_density")) for a in ctx.ad_ids}
    known = {a: d for a, d in dens.items() if d is not None}
    if not known:
        return []
    overall_med = float(np.median(list(known.values())))
    out = []
    for b, ids in ctx.by_brand().items():
        vals = {a: known[a] for a in ids if a in known}
        if not vals:
            continue
        arr = np.array(list(vals.values()))
        med, q1, q3 = float(np.median(arr)), float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
        out.append(_obs(ctx, f"text_density_median:{b}", f"brand:{b}",
                        f"Median OCR text density for {b} is {fmt(med, 'num')} (IQR {fmt(q1, 'num')}–{fmt(q3, 'num')}, "
                        f"n={len(vals)}), vs a dataset median of {fmt(overall_med, 'num')}.",
                        "text_density_median", med, "num", {"baseline": "dataset median", "value": overall_med},
                        len(vals), list(vals), "median and 25th/75th percentiles of text_density "
                        "(union area of OCR text boxes / image area)", ctx.caveats(len(vals), CAVEAT_OCR),
                        {"q1": q1, "q3": q3}))
        high = [a for a, d in vals.items() if d >= cfg.high_text_threshold]
        low = [a for a, d in vals.items() if d < cfg.low_text_threshold]
        share_high = len(high) / len(vals)
        base_high = sum(1 for d in known.values() if d >= cfg.high_text_threshold) / len(known)
        out.append(_obs(ctx, f"text_density_high:{b}", f"brand:{b}",
                        f"{len(high)} of {len(vals)} {b} creatives ({fmt(share_high, 'pct')}) are high-text "
                        f"(density ≥ {cfg.high_text_threshold}); {len(low)} are low-text (< {cfg.low_text_threshold}). "
                        f"Dataset high-text share: {fmt(base_high, 'pct')}.",
                        "high_text_share", share_high, "pct", {"baseline": "dataset high-text share", "value": base_high},
                        len(vals), high or list(vals), "count of text_density >= high threshold / brand records",
                        ctx.caveats(len(vals), CAVEAT_OCR),
                        {"high_text_ad_ids": sorted(high), "low_text_ad_ids": sorted(low),
                         "thresholds": {"high": cfg.high_text_threshold, "low": cfg.low_text_threshold}}))
    return out


def _mean_pairwise_tvd(vecs: List[np.ndarray]) -> Optional[float]:
    if len(vecs) < 2:
        return None
    d = [0.5 * float(np.abs(vecs[i] - vecs[j]).sum()) for i in range(len(vecs)) for j in range(i + 1, len(vecs))]
    return float(np.mean(d))


def analyse_colour(ctx) -> List[Observation]:
    cfg = ctx.cfg
    fam = {a: _family_shares(ctx.records[a]) for a in ctx.ad_ids}
    vec = {a: _colour_vec(ctx.records[a]) for a in ctx.ad_ids}
    known = [a for a in ctx.ad_ids if fam[a] is not None]
    if not known:
        return []
    overall_fam = {f: float(np.mean([fam[a][f] for a in known])) for f in HUE_FAMILIES}
    overall_tvd = _mean_pairwise_tvd([vec[a] for a in known])
    overall_white = sum(1 for a in known if fam[a]["white"] >= cfg.white_dominant_threshold) / len(known)
    out = []
    for b, ids in ctx.by_brand().items():
        ids = [a for a in ids if a in known]
        if not ids:
            continue
        mean_fam = {f: float(np.mean([fam[a][f] for a in ids])) for f in HUE_FAMILIES}
        top = sorted(CHROMATIC_FAMILIES, key=lambda f: (-mean_fam[f], f))[0]
        support = [a for a in ids if max(CHROMATIC_FAMILIES, key=lambda f: (fam[a][f], f)) == top]
        out.append(_obs(ctx, f"colour_family:{b}", f"brand:{b}",
                        f"The largest chromatic colour family in {b} creatives is {top}, covering on average "
                        f"{fmt(mean_fam[top], 'pct')} of pixels (dataset average {fmt(overall_fam[top], 'pct')}).",
                        "mean_colour_family_share", mean_fam[top], "pct",
                        {"baseline": "dataset mean share of the same family", "value": overall_fam[top]},
                        len(ids), support or ids, "mean over records of summed colour_distribution buckets per family",
                        ctx.caveats(len(ids), CAVEAT_COLOUR), {"mean_family_shares": mean_fam}))
        white = [a for a in ids if fam[a]["white"] >= cfg.white_dominant_threshold]
        sw = len(white) / len(ids)
        out.append(_obs(ctx, f"white_dominant:{b}", f"brand:{b}",
                        f"{len(white)} of {len(ids)} {b} creatives ({fmt(sw, 'pct')}) are white-dominant "
                        f"(≥ {fmt(cfg.white_dominant_threshold, 'pct')} near-white pixels), vs {fmt(overall_white, 'pct')} "
                        f"across the dataset.", "white_dominant_share", sw, "pct",
                        {"baseline": "dataset white-dominant share", "value": overall_white}, len(ids),
                        white or ids, "share of records with colour_distribution.white >= threshold",
                        ctx.caveats(len(ids), CAVEAT_COLOUR), {"white_dominant_ad_ids": sorted(white)}))
        tvd = _mean_pairwise_tvd([vec[a] for a in ids])
        if tvd is not None:
            out.append(_obs(ctx, f"palette_consistency:{b}", f"brand:{b}",
                            f"Mean pairwise colour-distribution distance within {b} is {fmt(tvd, 'num')} "
                            f"(0 = identical palettes, 1 = disjoint), vs {fmt(overall_tvd, 'num')} across all pairs "
                            f"in the dataset.", "palette_distance_intra_brand", tvd, "num",
                            {"baseline": "mean pairwise distance over all dataset pairs", "value": overall_tvd},
                            len(ids), ids, "mean total-variation distance between 15-bucket colour distributions",
                            ctx.caveats(len(ids), CAVEAT_COLOUR)))
    return out


def analyse_orientation(ctx) -> List[Observation]:
    get = lambda a: ctx.records[a].get("orientation")  # noqa: E731
    out = _distribution_obs(ctx, ctx.by_brand(), _scope_brand, get, "orientation_share", "orientation",
                            "count of orientation (square if |w/h-1|<=5%) per brand", [], "orientation")
    for o in out:
        b = o.scope.split(":", 1)[1]
        ars = [_num(ctx.records[a].get("aspect_ratio")) for a in ctx.by_brand()[b]]
        ars = [x for x in ars if x is not None]
        if ars:
            o.details["median_aspect_ratio"] = round(float(np.median(ars)), 4)
    return out


def _pair_sims(ctx, a_ids, b_ids, same=False) -> List[float]:
    sims = []
    for i, a in enumerate(a_ids):
        for b in (a_ids[i + 1:] if same else b_ids):
            sims.append(float(ctx.emb[a] @ ctx.emb[b]))
    return sims


def analyse_visual_consistency(ctx) -> List[Observation]:
    if not ctx.emb:
        return []
    out = []
    groups = {b: [a for a in ids if a in ctx.emb] for b, ids in ctx.by_brand().items()}
    for b, ids in groups.items():
        others = [a for g, v in groups.items() if g != b for a in v]
        if len(ids) < 2 or not others:
            continue
        intra = _pair_sims(ctx, ids, None, same=True)
        inter = _pair_sims(ctx, ids, others)
        mi, me = float(np.mean(intra)), float(np.mean(inter))
        out.append(_obs(ctx, f"clip_consistency:{b}", f"brand:{b}",
                        f"Mean CLIP cosine similarity between pairs of {b} creatives is {fmt(mi, 'num')} "
                        f"(sd {fmt(float(np.std(intra)), 'num')}, {len(intra)} pairs), vs {fmt(me, 'num')} between {b} "
                        f"and other brands' creatives ({len(inter)} pairs).", "clip_mean_intra_brand_cosine", mi, "num",
                        {"baseline": "mean cosine to other brands' creatives", "value": me}, len(ids), ids,
                        "mean pairwise cosine of L2-normalised CLIP image embeddings",
                        ctx.caveats(len(ids), CAVEAT_CLIP),
                        {"intra_sd": float(np.std(intra)), "inter_sd": float(np.std(inter)),
                         "n_intra_pairs": len(intra), "n_inter_pairs": len(inter)}))
    return out


def analyse_cross_brand(ctx) -> List[Observation]:
    out = []
    if ctx.emb:
        ids = [a for a in ctx.ad_ids if a in ctx.emb]
        pairs = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if ctx.brand[a] != ctx.brand[b]:
                    pairs.append((float(ctx.emb[a] @ ctx.emb[b]), *sorted((a, b))))
        pairs.sort(key=lambda p: (-p[0], p[1], p[2]))
        for rank, (s, a, b) in enumerate(pairs[:ctx.cfg.top_cross_brand_pairs], 1):
            out.append(_obs(ctx, f"cross_brand_pair:{rank}", "cross_brand",
                            f"Cross-brand pair #{rank} by CLIP similarity: {a} ({ctx.brand[a]}) and {b} "
                            f"({ctx.brand[b]}), cosine {fmt(s, 'num')}.", "clip_cosine", s, "num",
                            {"baseline": "rank among all cross-brand pairs", "value": len(pairs)}, 2, [a, b],
                            "pairwise cosine of CLIP embeddings, restricted to pairs from different brands",
                            [CAVEAT_GENERAL, CAVEAT_CLIP], comparative=False))
    for c, ids in ctx.by_cluster().items():
        if c == "noise":
            continue
        brands = Counter(ctx.brand[a] for a in ids)
        if len(brands) < 2:
            continue
        top, k = _top(brands)
        share = k / len(ids)
        out.append(_obs(ctx, f"mixed_cluster:{c}", f"cluster:{c}",
                        f"Cluster {c} mixes {len(brands)} brands across {len(ids)} creatives; the largest brand "
                        f"({top}) accounts for {fmt(share, 'pct')} (an even split would be {fmt(1 / len(brands), 'pct')}).",
                        "largest_brand_share_in_cluster", share, "pct",
                        {"baseline": "1/n_brands in cluster", "value": 1 / len(brands)}, len(ids), ids,
                        "brand counts among cluster members", ctx.caveats(len(ids), CAVEAT_CLUSTER),
                        {"brand_counts": dict(sorted(brands.items()))}))
    return out


def _numeric_matrix(ctx, ids) -> Dict[str, Dict[str, float]]:
    vals = {}
    for a in ids:
        r = ctx.records[a]
        row = {f: _num(r.get(f)) for f in NUMERIC_FEATURES}
        fam = _family_shares(r)
        if fam:
            row.update({f"colour_{k}": v for k, v in fam.items()})
        vals[a] = row
    return vals


def cluster_profiles(ctx) -> Dict[str, dict]:
    if not ctx.assign:
        return {}
    allvals = _numeric_matrix(ctx, ctx.ad_ids)
    feats = sorted({f for v in allvals.values() for f in v})
    stats = {}
    for f in feats:
        xs = [v[f] for v in allvals.values() if v.get(f) is not None]
        if len(xs) >= 2:
            stats[f] = (float(np.mean(xs)), float(np.std(xs)))
    profiles = {}
    for c, ids in ctx.by_cluster().items():
        prof = {"cluster": c, "size": len(ids), "ad_ids": ids,
                "brand_mix": dict(sorted(Counter(ctx.brand[a] for a in ids).items())),
                "layout_mix": dict(sorted(Counter(ctx.records[a].get("layout_category") or "missing" for a in ids).items())),
                "orientation_mix": dict(sorted(Counter(ctx.records[a].get("orientation") or "missing" for a in ids).items())),
                "cta_mix": dict(sorted(Counter(normalise_cta(_field(ctx.records[a], "cta")) for a in ids).items()))}
        dens = [_num(ctx.records[a].get("text_density")) for a in ids]
        dens = [d for d in dens if d is not None]
        prof["mean_text_density"] = round(float(np.mean(dens)), 4) if dens else None
        fams = [_family_shares(ctx.records[a]) for a in ids]
        fams = [f for f in fams if f]
        prof["mean_colour_families"] = {k: round(float(np.mean([f[k] for f in fams])), 4) for k in HUE_FAMILIES} if fams else None
        # distinguishing features: |z| of cluster mean vs dataset mean, in dataset-sd units
        dist = []
        for f, (mu, sd) in stats.items():
            xs = [allvals[a].get(f) for a in ids if allvals[a].get(f) is not None]
            if xs and sd > 0:
                m = float(np.mean(xs))
                dist.append({"feature": f, "cluster_mean": round(m, 4), "dataset_mean": round(mu, 4),
                             "z": round((m - mu) / sd, 3), "n": len(xs)})
        dist.sort(key=lambda d: (-abs(d["z"]), d["feature"]))
        prof["distinguishing_features"] = dist[:ctx.cfg.top_distinguishing_features]
        prof["representative_ad_ids"] = _representatives(ctx, ids)
        profiles[c] = prof
    return profiles


def _representatives(ctx, ids) -> List[str]:
    k = ctx.cfg.n_representatives
    emb_ids = [a for a in ids if a in ctx.emb]
    if emb_ids:
        centroid = np.mean([ctx.emb[a] for a in emb_ids], axis=0)
        return [a for _, a in sorted((-float(ctx.emb[a] @ centroid), a) for a in emb_ids)][:k]
    with_d = [(ctx.assign[a]["distance_to_centroid"], a) for a in ids if ctx.assign[a]["distance_to_centroid"] is not None]
    if with_d:
        return [a for _, a in sorted(with_d)][:k]
    return sorted(ids)[:k]


def analyse_clusters(ctx, profiles) -> List[Observation]:
    out = []
    for c, p in profiles.items():
        if c == "noise":
            out.append(_obs(ctx, "noise:dataset", "cluster:noise",
                            f"{p['size']} creatives were left unassigned as noise by the clustering algorithm.",
                            "n_noise", p["size"], "int", None, p["size"], p["ad_ids"],
                            "count of records with is_noise = true", [CAVEAT_GENERAL, CAVEAT_CLUSTER],
                            comparative=False))
            continue
        for d in p["distinguishing_features"]:
            out.append(_obs(ctx, f"cluster_feature:{c}:{d['feature']}", f"cluster:{c}",
                            f"Cluster {c} ({p['size']} creatives) has mean {d['feature']} of {fmt(d['cluster_mean'], 'num')} "
                            f"vs {fmt(d['dataset_mean'], 'num')} across the dataset (z = {d['z']:+.2f}).",
                            f"cluster_mean_{d['feature']}", d["cluster_mean"], "num",
                            {"baseline": "dataset mean", "value": d["dataset_mean"], "z": d["z"]},
                            d["n"], p["ad_ids"], "cluster mean minus dataset mean, divided by dataset sd; "
                            "top features by |z|", ctx.caveats(d["n"], CAVEAT_CLUSTER)))
    return out


def analyse_discovery(ctx) -> List[Observation]:
    cfg = ctx.cfg
    out = []
    groups = ctx.by_brand()
    # (1) offer / price wording visible in the creative (OCR, not metadata copy)
    has_text = {a: ctx.records[a].get("ocr_text") for a in ctx.ad_ids if ctx.records[a].get("ocr_text") is not None}
    if has_text:
        offer_all = [a for a, t in has_text.items() if OFFER_TEXT.search(t or "")]
        base = len(offer_all) / len(has_text)
        for b, ids in groups.items():
            ids = [a for a in ids if a in has_text]
            if not ids:
                continue
            hits = [a for a in ids if a in offer_all]
            s = len(hits) / len(ids)
            out.append(_obs(ctx, f"offer_text:{b}", f"brand:{b}",
                            f"{len(hits)} of {len(ids)} {b} creatives ({fmt(s, 'pct')}) show price/offer wording in the "
                            f"image itself (OCR), vs {fmt(base, 'pct')} across the dataset.", "offer_text_share", s, "pct",
                            {"baseline": "dataset share", "value": base}, len(ids), hits or ids,
                            "regex for ₹/Rs/%/offer/discount/MRP/coupon/price/off/sale/deal on ocr_text",
                            ctx.caveats(len(ids), CAVEAT_OCR), {"offer_text_ad_ids": sorted(hits)}))
    # (2) partnership advertisers (creator "with <brand>" ads)
    def is_partner(a):
        t = _field(ctx.records[a], "advertiser_type")
        adv = _field(ctx.records[a], "advertiser") or ""
        return t == "partnership" or " with " in adv
    have_adv = [a for a in ctx.ad_ids if _field(ctx.records[a], "advertiser") or _field(ctx.records[a], "advertiser_type")]
    if have_adv:
        for b, ids in groups.items():
            ids = [a for a in ids if a in have_adv]
            hits = [a for a in ids if is_partner(a)]
            if not ids or not hits:
                continue
            s = len(hits) / len(ids)
            out.append(_obs(ctx, f"partnership:{b}", f"brand:{b}",
                            f"{len(hits)} of {len(ids)} {b} creatives ({fmt(s, 'pct')}) were run as partnership ads "
                            f"(creator page \"with\" the brand).", "partnership_share", s, "pct", None, len(ids), hits,
                            "advertiser_type == partnership or advertiser contains ' with '",
                            ctx.caveats(len(ids)), comparative=False))
    # (3) low OCR readability: text detected but mostly not transcribed
    det = {a: (_num(ctx.records[a].get("ocr_n_text_regions")), _num(ctx.records[a].get("ocr_n_readable_regions")))
           for a in ctx.ad_ids}
    det = {a: v for a, v in det.items() if v[0] and v[1] is not None}
    if det:
        low = [a for a, (n, r) in det.items() if r / n < cfg.low_readability_ratio]
        s = len(low) / len(det)
        out.append(_obs(ctx, "low_ocr_readability:dataset", "dataset",
                        f"{len(low)} of {len(det)} creatives with detected text ({fmt(s, 'pct')}) had fewer than "
                        f"{fmt(cfg.low_readability_ratio, 'pct')} of text regions transcribed; this is consistent with "
                        f"non-Latin script (e.g. Devanagari) or stylised lettering.", "low_ocr_readability_share", s,
                        "pct", None, len(det), low or list(det),
                        "share of records with ocr_n_readable_regions / ocr_n_text_regions < threshold",
                        ctx.caveats(len(det), CAVEAT_OCR), {"low_readability_ad_ids": sorted(low)}, comparative=False))
    # (4) creative format mix (static vs video poster)
    fm = {a: _field(ctx.records[a], "image_type") for a in ctx.ad_ids}
    fm = {a: v for a, v in fm.items() if v}
    if fm:
        vid = [a for a, v in fm.items() if v == "video_thumbnail"]
        s = len(vid) / len(fm)
        out.append(_obs(ctx, "format_mix:dataset", "dataset",
                        f"{len(vid)} of {len(fm)} creatives ({fmt(s, 'pct')}) are video posters; the rest are static images.",
                        "video_poster_share", s, "pct", None, len(fm), vid or list(fm),
                        "share of image_type == video_thumbnail", ctx.caveats(len(fm)), comparative=False))
    return out


# ----------------------------------------------------------------------------- public API

def build_observations(bundle, assignments=None, out_dir: Union[None, str, Path] = None,
                       embeddings=None, config: Optional[IntelligenceConfig] = None) -> List[Observation]:
    """Compute all observations. When `out_dir` is given, also write observations.json,
    cluster_profiles.json and observations.md there."""
    cfg = config or IntelligenceConfig()
    ctx = _Ctx(bundle, assignments, embeddings, cfg)
    profiles = cluster_profiles(ctx)
    obs: List[Observation] = []
    for fn in (analyse_layouts, analyse_cta, analyse_text_density, analyse_colour, analyse_orientation,
               analyse_visual_consistency, analyse_cross_brand, analyse_discovery):
        obs.extend(fn(ctx))
    obs.extend(analyse_clusters(ctx, profiles))
    obs = [o for o in obs if o.supporting_ad_ids]
    check_statements(obs)
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        meta = {"n_records": len(ctx.ad_ids), "brands": ctx.brands, "n_with_embeddings": len(ctx.emb),
                "n_assigned": len(ctx.assign), "assignment_ids_not_in_bundle": ctx.unknown_assignment_ids,
                "config": cfg.to_dict(), "n_observations": len(obs),
                "n_insufficient_data": sum(o.status == "insufficient_data" for o in obs)}
        (out / "observations.json").write_text(json.dumps(
            {"meta": meta, "observations": [o.to_dict() for o in obs]}, indent=1, ensure_ascii=False))
        (out / "cluster_profiles.json").write_text(json.dumps(
            {"meta": {"n_clusters": sum(1 for c in profiles if c != "noise"), "config": cfg.to_dict()},
             "profiles": profiles}, indent=1, ensure_ascii=False))
        (out / "observations.md").write_text(render_markdown(obs, profiles, meta))
    return obs


def check_statements(obs: Iterable[Observation]) -> None:
    """Guardrail: statements must not make outcome/performance claims."""
    for o in obs:
        low = o.statement.lower()
        for term in BANNED_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", low):
                raise ValueError(f"observation {o.observation_id} uses banned term '{term}'")


def render_markdown(obs: List[Observation], profiles: Optional[Dict[str, dict]] = None,
                    meta: Optional[dict] = None) -> str:
    lines = ["# Creative Intelligence Observations", ""]
    if meta:
        lines += [f"Records: {meta['n_records']} · brands: {', '.join(meta['brands'])} · "
                  f"with CLIP embeddings: {meta['n_with_embeddings']} · clustered: {meta['n_assigned']} · "
                  f"observations: {meta['n_observations']} ({meta['n_insufficient_data']} flagged insufficient data)", ""]
    lines += ["Every statement is generated from the numbers shown and lists the ads it rests on. "
              "Observations describe creative appearance only.", ""]
    scopes = defaultdict(list)
    for o in obs:
        scopes[o.scope.split(":")[0]].append(o)
    titles = {"dataset": "Dataset-wide", "brand": "By brand", "cluster": "By cluster", "cross_brand": "Cross-brand"}
    for key in ("dataset", "brand", "cross_brand", "cluster"):
        if key not in scopes:
            continue
        lines += [f"## {titles[key]}", ""]
        for o in sorted(scopes[key], key=lambda o: (o.scope, o.observation_id)):
            flag = " ⚠️ insufficient data" if o.status == "insufficient_data" else ""
            ids = ", ".join(o.supporting_ad_ids[:8]) + (f" … (+{len(o.supporting_ad_ids) - 8})" if len(o.supporting_ad_ids) > 8 else "")
            lines += [f"- **{o.scope}**: {o.statement}{flag}  ",
                      f"  _metric_ `{o.metric}` · n={o.n} · ads: {ids}"]
        lines.append("")
    if profiles:
        lines += ["## Cluster profiles", "",
                  "| Cluster | Size | Brands | Top layout | Mean text density | Representatives |",
                  "|---|---|---|---|---|---|"]
        for c, p in profiles.items():
            top_layout = _top(Counter(p["layout_mix"]))[0] if p["layout_mix"] else "—"
            lines.append(f"| {c} | {p['size']} | {', '.join(f'{b} {n}' for b, n in p['brand_mix'].items())} | "
                         f"{top_layout} | {fmt(p['mean_text_density'], 'num')} | {', '.join(p['representative_ad_ids'])} |")
        lines.append("")
    lines += ["## Standing caveats", "", f"- {CAVEAT_GENERAL}", f"- {CAVEAT_LAYOUT}", f"- {CAVEAT_OCR}",
              f"- {CAVEAT_CLIP}", f"- {CAVEAT_COLOUR}", ""]
    return "\n".join(lines)

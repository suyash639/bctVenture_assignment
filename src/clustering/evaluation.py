"""
Stability analysis, parameter sweeps and multi-criteria configuration selection.

Stability (all on the same matrix X, fixed seeds):
  seed_ari       mean pairwise ARI between runs with different seeds (k-means only;
                 deterministic algorithms report None, not a trivial 1.0)
  subsample_ari  mean ARI between the full-data labelling and labellings fitted on
                 random 80% subsamples, compared on the shared points (all algorithms)
  neighbour_ari  mean ARI against the same algorithm/linkage at k-1 and k+1 (informational:
                 high values mean the partition changes gradually with k)

Selection (select_configuration) never uses one metric alone. Each eligible configuration
is ranked on silhouette (higher), Davies-Bouldin (lower), Calinski-Harabasz (higher) and
stability (higher, subsample ARI); ranks are averaged, then structural penalties are added:
tiny clusters (< MIN_CLUSTER_SIZE members), noise share > MAX_NOISE_SHARE, or one cluster
holding > MAX_LARGEST_SHARE of all records. Each penalty adds the number of eligible
configurations to the score, pushing violators below every clean configuration.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np

from src.clustering.core import ClusterConfig, ClusteringResult, run_clustering

MIN_CLUSTER_SIZE = 3
MAX_NOISE_SHARE = 0.30
MAX_LARGEST_SHARE = 0.60
SMALL_N_HDBSCAN = 50


def _ari(a, b) -> float:
    from sklearn.metrics import adjusted_rand_score
    return float(adjusted_rand_score(a, b))


def seed_stability(X, ad_ids, config: ClusterConfig, seeds: Sequence[int]) -> Optional[float]:
    if not config.seeded or len(seeds) < 2:
        return None
    labs = [run_clustering(X, ad_ids, config.with_seed(s)).labels for s in seeds]
    return round(float(np.mean([_ari(a, b) for a, b in itertools.combinations(labs, 2)])), 4)


def subsample_stability(X, ad_ids, config: ClusterConfig, reference: np.ndarray,
                        n_boot: int = 10, frac: float = 0.8, seed: int = 0) -> Optional[float]:
    X = np.asarray(X)
    n = X.shape[0]
    m = int(round(n * frac))
    if m < 4 or n_boot < 1:
        return None
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n_boot):
        idx = np.sort(rng.choice(n, size=m, replace=False))
        try:
            sub = run_clustering(X[idx], [ad_ids[i] for i in idx], config)
        except ValueError:
            continue
        scores.append(_ari(reference[idx], sub.labels))
    return round(float(np.mean(scores)), 4) if scores else None


@dataclass
class SweepEntry:
    config: ClusterConfig
    result: Optional[ClusteringResult] = None
    stability: Dict[str, Optional[float]] = field(default_factory=dict)
    error: Optional[str] = None

    def summary(self) -> Dict[str, Any]:
        return {"config": self.config.to_dict(), "error": self.error,
                "metrics": None if self.result is None else self.result.metrics,
                "stability": self.stability}


@dataclass
class SweepResult:
    ad_ids: List[str]
    entries: List[SweepEntry]
    brands: Dict[str, Optional[str]] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def get(self, config_id: str) -> SweepEntry:
        return next(e for e in self.entries if e.config.config_id == config_id)

    def to_dict(self) -> Dict[str, Any]:
        return {"n_records": len(self.ad_ids), "notes": self.notes,
                "entries": [e.summary() for e in self.entries]}


def default_grid(n: int, seed: int = 0, k_range: Iterable[int] = range(2, 9),
                 hdbscan_sizes: Iterable[int] = range(3, 7)) -> List[ClusterConfig]:
    ks = [k for k in k_range if 2 <= k <= n - 1]
    grid = [ClusterConfig("kmeans", {"n_clusters": k, "n_init": 10}, seed) for k in ks]
    grid += [ClusterConfig("agglomerative", {"n_clusters": k, "linkage": "ward"}, seed) for k in ks]
    grid += [ClusterConfig("agglomerative", {"n_clusters": k, "linkage": "average", "metric": "cosine"}, seed)
             for k in ks]
    grid += [ClusterConfig("hdbscan", {"min_cluster_size": s}, seed) for s in hdbscan_sizes if s <= n // 2]
    return grid


def _brands_of(fm) -> Dict[str, Optional[str]]:
    ids = list(fm.ad_ids)
    if getattr(fm, "brands", None) is not None:
        b = fm.brands
        return dict(b) if isinstance(b, dict) else dict(zip(ids, b))
    recs = getattr(fm, "records", None) or {}
    out = {}
    for a in ids:
        r = recs.get(a) or {}
        out[a] = r.get("brand") or (r.get("dataset") or {}).get("brand")
    return out


def run_sweep(fm, configs: Optional[List[ClusterConfig]] = None, stability_seeds: Sequence[int] = (0, 1, 2, 3, 4),
              n_boot: int = 10, subsample_frac: float = 0.8, seed: int = 0) -> SweepResult:
    """Fit every config on fm.X; record metrics + stability; failures are recorded, not raised."""
    X, ad_ids = np.asarray(fm.X, dtype=np.float64), list(fm.ad_ids)
    configs = configs if configs is not None else default_grid(len(ad_ids), seed)
    entries: List[SweepEntry] = []
    for cfg in configs:
        e = SweepEntry(cfg)
        try:
            e.result = run_clustering(X, ad_ids, cfg)
            e.stability = {
                "seed_ari": seed_stability(X, ad_ids, cfg, stability_seeds),
                "subsample_ari": subsample_stability(X, ad_ids, cfg, e.result.labels, n_boot, subsample_frac, seed),
            }
        except ValueError as ex:
            e.error = str(ex)
        entries.append(e)
    _neighbour_ari(entries)
    notes = []
    if len(ad_ids) < SMALL_N_HDBSCAN and any(c.algorithm == "hdbscan" for c in configs):
        notes.append(f"n={len(ad_ids)} < {SMALL_N_HDBSCAN}: HDBSCAN density estimates rest on very few points "
                     "per cluster; expect high noise shares or a single cluster. Its results are reported, "
                     "not forced.")
    return SweepResult(ad_ids, entries, _brands_of(fm), notes)


def _neighbour_ari(entries: List[SweepEntry]) -> None:
    def family(c: ClusterConfig):
        return (c.algorithm, tuple(sorted((k, v) for k, v in c.params.items() if k != "n_clusters")))
    by = {}
    for e in entries:
        if e.result is not None and "n_clusters" in e.config.params:
            by[(family(e.config), int(e.config.params["n_clusters"]))] = e
    for (fam, k), e in by.items():
        vals = [_ari(e.result.labels, by[(fam, kk)].result.labels) for kk in (k - 1, k + 1) if (fam, kk) in by]
        e.stability["neighbour_ari"] = round(float(np.mean(vals)), 4) if vals else None
    for e in entries:
        e.stability.setdefault("neighbour_ari", None)


@dataclass
class Selection:
    config: Optional[ClusterConfig]
    rationale: str
    table: List[Dict[str, Any]]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"selected_config": None if self.config is None else self.config.to_dict(),
                "rationale": self.rationale, "warnings": self.warnings, "ranking": self.table}


def _rank(values: List[float], higher_better: bool) -> List[float]:
    from scipy.stats import rankdata
    v = np.asarray(values, dtype=float)
    return list(rankdata(-v if higher_better else v, method="average"))


def select_configuration(sweep: SweepResult, min_cluster_size: int = MIN_CLUSTER_SIZE,
                         max_noise_share: float = MAX_NOISE_SHARE,
                         max_largest_share: float = MAX_LARGEST_SHARE) -> Selection:
    eligible, table = [], []
    for e in sweep.entries:
        m = e.result.metrics if e.result is not None else None
        row = {"config_id": e.config.config_id, "algorithm": e.config.algorithm}
        if e.error:
            row.update(status="failed", reason=e.error)
        elif m["silhouette"] is None:
            row.update(status="ineligible", reason=m.get("metrics_undefined_reason", "metrics undefined"),
                       n_clusters=m["n_clusters"], noise_share=m["noise_share"])
        else:
            eligible.append(e)
            continue
        table.append(row)
    if not eligible:
        return Selection(None, "No configuration produced >= 2 clusters with defined metrics; no selection made.",
                         table, ["no eligible configuration"])

    stab = [e.stability.get("subsample_ari") for e in eligible]
    stab_vals = [s if s is not None else -1.0 for s in stab]
    sil = _rank([e.result.metrics["silhouette"] for e in eligible], True)
    db = _rank([e.result.metrics["davies_bouldin"] for e in eligible], False)
    ch = _rank([e.result.metrics["calinski_harabasz"] for e in eligible], True)
    st = _rank(stab_vals, True)
    n_el = len(eligible)
    scored = []
    for i, e in enumerate(eligible):
        m = e.result.metrics
        pen = []
        if m["min_cluster_size"] < min_cluster_size:
            pen.append(f"cluster smaller than {min_cluster_size} (min size {m['min_cluster_size']})")
        if m["noise_share"] > max_noise_share:
            pen.append(f"noise share {m['noise_share']:.0%} > {max_noise_share:.0%}")
        if m["largest_cluster_share"] > max_largest_share:
            pen.append(f"largest cluster holds {m['largest_cluster_share']:.0%} > {max_largest_share:.0%}")
        mean_rank = (sil[i] + db[i] + ch[i] + st[i]) / 4
        score = mean_rank + n_el * len(pen)
        scored.append((score, -stab_vals[i], m["n_clusters"], e.config.config_id, e, pen,
                       {"silhouette": sil[i], "davies_bouldin": db[i], "calinski_harabasz": ch[i], "stability": st[i]}))
    scored.sort(key=lambda t: t[:4])
    for score, _, _, cid, e, pen, ranks in scored:
        m = e.result.metrics
        table.append({"config_id": cid, "algorithm": e.config.algorithm, "status": "eligible",
                      "score": round(score, 3), "ranks": ranks, "penalties": pen,
                      "n_clusters": m["n_clusters"], "noise_share": m["noise_share"],
                      "silhouette": m["silhouette"], "davies_bouldin": m["davies_bouldin"],
                      "calinski_harabasz": m["calinski_harabasz"], "stability": e.stability,
                      "cluster_sizes": m["cluster_sizes"]})
    best = scored[0]
    e, pen, ranks = best[4], best[5], best[6]
    m = e.result.metrics
    best_sil = max(eligible, key=lambda x: x.result.metrics["silhouette"])
    lines = [
        f"Selected {e.config.config_id} (score {best[0]:.2f}; lower is better) out of {n_el} eligible "
        f"configurations ({len(sweep.entries) - n_el} failed or had undefined metrics).",
        f"Criteria ranks (1 = best of {n_el}): silhouette {ranks['silhouette']:.1f}, Davies-Bouldin "
        f"{ranks['davies_bouldin']:.1f}, Calinski-Harabasz {ranks['calinski_harabasz']:.1f}, "
        f"stability {ranks['stability']:.1f}.",
        f"Values: silhouette {m['silhouette']:.3f}, Davies-Bouldin {m['davies_bouldin']:.3f}, "
        f"Calinski-Harabasz {m['calinski_harabasz']:.1f}, subsample ARI {e.stability.get('subsample_ari')}, "
        f"{m['n_clusters']} clusters, sizes {sorted(m['cluster_sizes'].values(), reverse=True)}, "
        f"noise {m['noise_share']:.0%}.",
        "Structural penalties: " + ("; ".join(pen) if pen else "none") + ".",
    ]
    if best_sil.config.config_id != e.config.config_id:
        bm = best_sil.result.metrics
        bpen = next(t[5] for t in scored if t[4] is best_sil)
        lines.append(f"The highest-silhouette configuration, {best_sil.config.config_id} "
                     f"(silhouette {bm['silhouette']:.3f}), was not chosen: "
                     + ("; ".join(bpen) if bpen else "it ranked lower on the other criteria") + ".")
    if len(scored) > 1:
        lines.append("Runners-up: " + ", ".join(f"{t[3]} ({t[0]:.2f})" for t in scored[1:4]) + ".")
    warnings = []
    if m["silhouette"] < 0.1:
        warnings.append(f"silhouette {m['silhouette']:.3f} < 0.10: weak cluster structure; treat clusters as "
                        "soft groupings, not distinct types.")
    if pen:
        warnings.append("every eligible configuration violated at least one structural rule; "
                        "the least-penalised one was selected.")
    if e.stability.get("subsample_ari") is not None and e.stability["subsample_ari"] < 0.5:
        warnings.append(f"subsample ARI {e.stability['subsample_ari']:.2f} < 0.5: assignments are not stable "
                        "under resampling.")
    warnings += sweep.notes
    return Selection(e.config, " ".join(lines), table, warnings)

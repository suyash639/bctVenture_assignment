"""
Clustering core: configuration, fitting, and internal-validity metrics.

Algorithms
  kmeans         sklearn KMeans (k-means++ init, n_init restarts, seeded)
  agglomerative  sklearn AgglomerativeClustering (ward | average | complete | single);
                 ward is Euclidean-only, other linkages default to cosine
  hdbscan        sklearn.cluster.HDBSCAN (density based; label -1 = noise, never forced)

Metrics are computed on non-noise points only and are None when undefined
(fewer than 2 clusters, or every point in its own cluster).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

ALGORITHMS = ("kmeans", "agglomerative", "hdbscan")


@dataclass
class ClusterConfig:
    algorithm: str
    params: Dict[str, Any] = field(default_factory=dict)
    seed: int = 0

    def __post_init__(self):
        if self.algorithm not in ALGORITHMS:
            raise ValueError(f"unknown algorithm '{self.algorithm}', expected one of {ALGORITHMS}")
        self.params = dict(self.params or {})

    @property
    def config_id(self) -> str:
        """Deterministic id: algorithm + sorted params (seed excluded: it is a run property)."""
        parts = [f"{k}={self.params[k]}" for k in sorted(self.params)]
        return self.algorithm + ("|" + ",".join(parts) if parts else "")

    @property
    def metric(self) -> str:
        if self.algorithm == "agglomerative":
            linkage = self.params.get("linkage", "ward")
            return "euclidean" if linkage == "ward" else self.params.get("metric", "cosine")
        return self.params.get("metric", "euclidean")

    @property
    def seeded(self) -> bool:
        """Whether the seed changes the result (only k-means is stochastic here)."""
        return self.algorithm == "kmeans"

    def with_seed(self, seed: int) -> "ClusterConfig":
        return ClusterConfig(self.algorithm, dict(self.params), seed)

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "config_id": self.config_id, "metric": self.metric}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ClusterConfig":
        return cls(d["algorithm"], d.get("params", {}), d.get("seed", 0))


@dataclass
class ClusteringResult:
    ad_ids: List[str]
    labels: np.ndarray                         # int, -1 = noise
    config: ClusterConfig
    metrics: Dict[str, Any]
    probabilities: Optional[np.ndarray] = None  # HDBSCAN membership strength, else None
    distance_to_centroid: Optional[np.ndarray] = None  # NaN for noise

    def to_assignments(self, brands: Optional[Dict[str, Optional[str]]] = None) -> List[Dict[str, Any]]:
        """Exactly one row per input ad_id, noise included (cluster_id = -1)."""
        brands = brands or {}
        rows = []
        for i, a in enumerate(self.ad_ids):
            lab = int(self.labels[i])
            d = None if self.distance_to_centroid is None else self.distance_to_centroid[i]
            p = None if self.probabilities is None else float(self.probabilities[i])
            rows.append({
                "ad_id": a, "brand": brands.get(a), "cluster_id": lab, "is_noise": lab == -1,
                "algorithm": self.config.algorithm, "config_id": self.config.config_id,
                "distance_to_centroid": None if d is None or not np.isfinite(d) else round(float(d), 6),
                "membership_probability": None if p is None else round(p, 6),
            })
        return rows


def _validate(X: np.ndarray, ad_ids: Sequence[str]) -> np.ndarray:
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError(f"X must be 2-D, got shape {X.shape}")
    if len(ad_ids) != X.shape[0]:
        raise ValueError(f"len(ad_ids)={len(ad_ids)} does not match X rows={X.shape[0]}")
    if len(set(ad_ids)) != len(ad_ids):
        raise ValueError("ad_ids must be unique (one ad = one row)")
    if not np.all(np.isfinite(X)):
        bad = [ad_ids[i] for i in np.where(~np.all(np.isfinite(X), axis=1))[0]]
        raise ValueError(f"X contains non-finite values for ad_ids {bad[:10]}")
    if X.shape[0] < 2:
        raise ValueError("need at least 2 records to cluster")
    return X


def _fit(X: np.ndarray, cfg: ClusterConfig):
    p = cfg.params
    n = X.shape[0]
    if cfg.algorithm == "kmeans":
        from sklearn.cluster import KMeans
        k = int(p.get("n_clusters", 3))
        if not 1 <= k <= n:
            raise ValueError(f"n_clusters={k} invalid for n={n}")
        m = KMeans(n_clusters=k, n_init=int(p.get("n_init", 10)), random_state=cfg.seed).fit(X)
        return m.labels_.astype(int), None
    if cfg.algorithm == "agglomerative":
        from sklearn.cluster import AgglomerativeClustering
        linkage = p.get("linkage", "ward")
        kw = {"linkage": linkage, "metric": cfg.metric}
        if p.get("distance_threshold") is not None:
            kw.update(n_clusters=None, distance_threshold=float(p["distance_threshold"]), compute_full_tree=True)
        else:
            k = int(p.get("n_clusters", 3))
            if not 1 <= k <= n:
                raise ValueError(f"n_clusters={k} invalid for n={n}")
            kw["n_clusters"] = k
        m = AgglomerativeClustering(**kw).fit(X)
        return m.labels_.astype(int), None
    from sklearn.cluster import HDBSCAN
    mcs = int(p.get("min_cluster_size", 5))
    if mcs > n:
        raise ValueError(f"min_cluster_size={mcs} > n={n}")
    ms = p.get("min_samples")
    kw = {}
    import inspect
    if "copy" in inspect.signature(HDBSCAN).parameters:
        kw["copy"] = True  # never modify the caller's matrix (and silences a sklearn FutureWarning)
    m = HDBSCAN(min_cluster_size=mcs, min_samples=None if ms is None else int(ms),
                metric=cfg.metric, cluster_selection_method=p.get("cluster_selection_method", "eom"),
                allow_single_cluster=bool(p.get("allow_single_cluster", False)), **kw).fit(X)
    return m.labels_.astype(int), np.asarray(m.probabilities_, dtype=float)


def compute_metrics(X: np.ndarray, labels: np.ndarray, metric: str = "euclidean") -> Dict[str, Any]:
    """Internal validity metrics on non-noise points; None where a metric is undefined."""
    from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
    labels = np.asarray(labels)
    n = len(labels)
    mask = labels >= 0
    clean = labels[mask]
    uniq, counts = np.unique(clean, return_counts=True)
    k = len(uniq)
    sizes = {int(u): int(c) for u, c in zip(uniq, counts)}
    out: Dict[str, Any] = {
        "n_records": int(n), "n_clusters": int(k), "n_noise": int((~mask).sum()),
        "noise_share": round(float((~mask).mean()), 4) if n else 0.0,
        "cluster_sizes": sizes,
        "min_cluster_size": int(counts.min()) if k else 0,
        "max_cluster_size": int(counts.max()) if k else 0,
        "largest_cluster_share": round(float(counts.max() / n), 4) if k else 0.0,
        "n_singleton_clusters": int((counts == 1).sum()),
        "silhouette": None, "davies_bouldin": None, "calinski_harabasz": None,
        "silhouette_metric": metric,
    }
    n_clean = int(mask.sum())
    if k < 2 or k >= n_clean:
        out["metrics_undefined_reason"] = (
            f"{k} cluster(s) among {n_clean} non-noise points: internal metrics need 2 <= k <= n-1")
        return out
    Xc = X[mask]
    out["silhouette"] = round(float(silhouette_score(Xc, clean, metric=metric)), 6)
    out["davies_bouldin"] = round(float(davies_bouldin_score(Xc, clean)), 6)
    out["calinski_harabasz"] = round(float(calinski_harabasz_score(Xc, clean)), 6)
    return out


def _centroid_distances(X: np.ndarray, labels: np.ndarray) -> np.ndarray:
    d = np.full(len(labels), np.nan)
    for lab in np.unique(labels):
        if lab < 0:
            continue
        idx = labels == lab
        c = X[idx].mean(axis=0)
        d[idx] = np.linalg.norm(X[idx] - c, axis=1)
    return d


def run_clustering(X: np.ndarray, ad_ids: Sequence[str], config: ClusterConfig) -> ClusteringResult:
    X = _validate(X, ad_ids)
    labels, probs = _fit(X, config)
    return ClusteringResult(ad_ids=list(ad_ids), labels=labels, config=config,
                            metrics=compute_metrics(X, labels, config.metric),
                            probabilities=probs, distance_to_centroid=_centroid_distances(X, labels))


def to_json(obj) -> str:
    def default(o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, ClusterConfig):
            return o.to_dict()
        raise TypeError(f"not JSON serialisable: {type(o)}")
    return json.dumps(obj, indent=1, default=default, ensure_ascii=False)

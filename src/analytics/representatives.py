"""
Representative creatives per cluster: the k members closest (Euclidean, in the fused feature
space fm.X used for clustering) to their cluster centroid. Ties break by ad_id, so the
selection is deterministic. Noise / unassigned ads have no centroid and get no representatives;
members missing from the feature matrix are reported, not dropped.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from src.analytics.common import NOISE, AnalyticsInput, cluster_label


def centroid_distances(inp: AnalyticsInput, fm) -> Dict[str, float]:
    """ad_id -> distance to own cluster centroid (only clustered ads present in fm)."""
    row = {str(a): i for i, a in enumerate(fm.ad_ids)}
    X = np.asarray(fm.X, dtype=np.float64)
    out: Dict[str, float] = {}
    for c in inp.ordered_clusters:
        if c in (None, NOISE):
            continue
        members = [a for a in inp.members(c) if a in row]
        if not members:
            continue
        M = X[[row[a] for a in members]]
        centre = M.mean(axis=0)
        for a, d in zip(members, np.linalg.norm(M - centre, axis=1)):
            out[a] = float(d)
    return out


def select_representatives(inp: AnalyticsInput, fm, k: int = 3) -> Dict[str, dict]:
    """{cluster_label: {"cluster_id", "representatives": [{ad_id, brand, distance}], "not_in_matrix": [...]}}"""
    dist = centroid_distances(inp, fm)
    out = {}
    for c in inp.ordered_clusters:
        if c in (None, NOISE):
            continue
        members = inp.members(c)
        ranked = sorted((a for a in members if a in dist), key=lambda a: (round(dist[a], 9), a))
        out[cluster_label(c)] = {
            "cluster_id": c, "size": len(members),
            "representatives": [{"ad_id": a, "brand": inp.brands[a], "distance_to_centroid": round(dist[a], 6)}
                                for a in ranked[:k]],
            "not_in_matrix": [a for a in members if a not in dist],
        }
    return out


def representative_rows(reps: Dict[str, dict]) -> List[dict]:
    return [{"cluster": lab, "rank": i + 1, **r} for lab, v in reps.items() for i, r in enumerate(v["representatives"])]

"""
2-D projections of the fused feature matrix (fm.X): PCA always, UMAP only if umap-learn is
installed. Points are coloured by cluster and shaped by brand; the sibling CSV gives the
coordinates of every ad_id. PCA uses the full SVD solver and a sign convention (largest
absolute loading of each component positive), so coordinates are reproducible run to run.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np

from src.analytics.common import (
    BRAND_MARKERS,
    AnalyticsInput,
    Manifest,
    cluster_colour,
    cluster_label,
    save_fig,
    setup_matplotlib,
    write_csv,
)


def _rows_in_matrix(inp: AnalyticsInput, fm):
    row = {str(a): i for i, a in enumerate(fm.ad_ids)}
    present = [a for a in inp.ad_ids if a in row]
    missing = [{"ad_id": a, "reason": "not in feature matrix (excluded during feature fusion)"}
               for a in inp.ad_ids if a not in row]
    X = np.asarray(fm.X, dtype=np.float64)[[row[a] for a in present]] if present else np.zeros((0, 0))
    return present, X, missing


def pca_2d(X: np.ndarray, seed: int = 0):
    from sklearn.decomposition import PCA
    p = PCA(n_components=2, svd_solver="full", random_state=seed)
    Z = p.fit_transform(X)
    for j in range(2):  # deterministic sign
        if p.components_[j][np.argmax(np.abs(p.components_[j]))] < 0:
            Z[:, j] *= -1
    return Z, [float(v) for v in p.explained_variance_ratio_]


def umap_available() -> bool:
    try:
        import umap  # noqa: F401
        return True
    except Exception:
        return False


def _scatter(inp: AnalyticsInput, ad_ids: List[str], Z: np.ndarray, title: str, xlabel: str, ylabel: str, png: Path):
    plt = setup_matplotlib()
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    brands = inp.ordered_brands
    for c in inp.ordered_clusters:
        for bi, b in enumerate(brands):
            idx = [i for i, a in enumerate(ad_ids) if inp.clusters[a] == c and inp.brands[a] == b]
            if not idx:
                continue
            col = cluster_colour(c, inp.ordered_clusters)
            hollow = c is None  # unassigned: hollow marker so it never reads as a cluster
            ax.scatter(Z[idx, 0], Z[idx, 1], s=70, facecolors="none" if hollow else col,
                       edgecolors="#666666" if hollow else "white", linewidths=1.2 if hollow else 0.6,
                       marker=BRAND_MARKERS[bi % len(BRAND_MARKERS)], alpha=0.9 if c not in (None, -1) else 0.7)
    from matplotlib.lines import Line2D
    ch = [Line2D([], [], marker="o", ls="", color=cluster_colour(c, inp.ordered_clusters), label=cluster_label(c))
          for c in inp.ordered_clusters]
    bh = [Line2D([], [], marker=BRAND_MARKERS[i % len(BRAND_MARKERS)], ls="", color="#444444", label=b)
          for i, b in enumerate(brands)]
    leg1 = ax.legend(handles=ch, title="cluster", loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
    ax.add_artist(leg1)
    ax.legend(handles=bh, title="brand", loc="lower left", bbox_to_anchor=(1.01, 0), frameon=False)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    save_fig(fig, png)


def projection_plots(inp: AnalyticsInput, fm, out_dir: Path, manifest: Manifest, seed: int = 0) -> List[dict]:
    out_dir = Path(out_dir) / "projections"
    present, X, missing = _rows_in_matrix(inp, fm)
    entries = []
    png, csvp = out_dir / "pca_2d.png", out_dir / "pca_2d.csv"
    if len(present) < 3:
        entries.append(manifest.add(None, "projection_pca", "PCA 2-D projection", covered=[],
                                    missing=missing + [{"ad_id": a, "reason": "fewer than 3 points; PCA skipped"}
                                                       for a in present], status="skipped: fewer than 3 records"))
    else:
        Z, evr = pca_2d(X, seed)
        _scatter(inp, present, Z, f"PCA of fused features (n={len(present)})",
                 f"PC1 ({evr[0]:.0%} var.)", f"PC2 ({evr[1]:.0%} var.)", png)
        write_csv(csvp, [{"ad_id": a, "brand": inp.brands[a], "cluster": cluster_label(inp.clusters[a]),
                          "x": round(float(Z[i, 0]), 6), "y": round(float(Z[i, 1]), 6)} for i, a in enumerate(present)])
        entries.append(manifest.add(png, "projection_pca", "PCA 2-D of fm.X; colour = cluster, marker = brand",
                                    covered=present, missing=missing, mapping=csvp,
                                    extra={"explained_variance_ratio": [round(v, 4) for v in evr]}))
    if not umap_available():
        entries.append(manifest.add(None, "projection_umap", "UMAP 2-D projection", covered=[],
                                    missing=[{"ad_id": a, "reason": "umap-learn not installed"} for a in inp.ad_ids],
                                    status="skipped: umap-learn not installed"))
    elif len(present) < 5:
        entries.append(manifest.add(None, "projection_umap", "UMAP 2-D projection", covered=[],
                                    missing=missing + [{"ad_id": a, "reason": "fewer than 5 points; UMAP skipped"}
                                                       for a in present], status="skipped: fewer than 5 records"))
    else:
        import umap
        Z = umap.UMAP(n_components=2, random_state=seed, n_neighbors=min(15, len(present) - 1),
                      metric="euclidean").fit_transform(X)
        png, csvp = out_dir / "umap_2d.png", out_dir / "umap_2d.csv"
        _scatter(inp, present, Z, f"UMAP of fused features (n={len(present)})", "UMAP-1", "UMAP-2", png)
        write_csv(csvp, [{"ad_id": a, "brand": inp.brands[a], "cluster": cluster_label(inp.clusters[a]),
                          "x": round(float(Z[i, 0]), 6), "y": round(float(Z[i, 1]), 6)} for i, a in enumerate(present)])
        entries.append(manifest.add(png, "projection_umap", "UMAP 2-D of fm.X (random_state fixed)",
                                    covered=present, missing=missing, mapping=csvp))
    return entries

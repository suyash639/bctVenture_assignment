"""
Distribution charts. Each chart has a sibling CSV with one row per ad_id (the value it
contributes and where it is drawn); ads with a null value are listed as missing with a reason.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Callable, List, Tuple

import numpy as np

from src.analytics.common import (
    NOISE_COLOUR,
    OKABE_ITO,
    AnalyticsInput,
    Manifest,
    cluster_colour,
    cluster_label,
    save_fig,
    setup_matplotlib,
    write_csv,
)

LAYOUTS = ["product_focused", "lifestyle", "testimonial", "offer_heavy", "educational", "unknown"]
ORIENTATIONS = ["portrait", "square", "landscape"]


def _field(inp: AnalyticsInput, ad: str, name: str):
    rec = inp.records.get(ad, {})
    v = rec.get(name)
    return v if v is not None else (rec.get("dataset") or {}).get(name)


def _split(inp: AnalyticsInput, name: str, valid: Callable = lambda v: v is not None):
    ok, missing = [], []
    for a in inp.ad_ids:
        v = _field(inp, a, name)
        (ok if valid(v) else missing).append(a)
    return ok, [{"ad_id": a, "reason": f"{name} is null / invalid"} for a in missing]


def cluster_size_chart(inp: AnalyticsInput, out_dir: Path, manifest: Manifest) -> dict:
    plt = setup_matplotlib()
    labs = [cluster_label(c) for c in inp.ordered_clusters]
    sizes = [len(inp.members(c)) for c in inp.ordered_clusters]
    fig, ax = plt.subplots(figsize=(max(5, 0.6 * len(labs) + 2), 4))
    bars = ax.bar(labs, sizes, color=[cluster_colour(c, inp.ordered_clusters) for c in inp.ordered_clusters])
    ax.bar_label(bars, padding=2)
    ax.set_ylabel("ads")
    ax.set_title(f"Cluster sizes (n={len(inp.ad_ids)})")
    png = save_fig(fig, Path(out_dir) / "distributions" / "cluster_sizes.png")
    mp = write_csv(Path(out_dir) / "distributions" / "cluster_sizes.csv",
                   [{"ad_id": a, "brand": inp.brands[a], "cluster": cluster_label(inp.clusters[a])} for a in inp.ad_ids])
    return manifest.add(png, "cluster_size", "Number of ads per cluster (noise/unassigned shown separately)",
                        covered=inp.ad_ids, mapping=mp, extra={"sizes": dict(zip(labs, sizes))})


def brand_cluster_matrix(inp: AnalyticsInput, out_dir: Path, manifest: Manifest) -> dict:
    plt = setup_matplotlib()
    brands, clusters = inp.ordered_brands, inp.ordered_clusters
    M = np.array([[sum(1 for a in inp.ad_ids if inp.brands[a] == b and inp.clusters[a] == c) for c in clusters]
                  for b in brands])
    fig, ax = plt.subplots(figsize=(max(5, 0.7 * len(clusters) + 3), 0.55 * len(brands) + 2))
    im = ax.imshow(M, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(clusters)), [cluster_label(c) for c in clusters])
    ax.set_yticks(range(len(brands)), brands)
    for i in range(len(brands)):
        for j in range(len(clusters)):
            ax.text(j, i, str(M[i, j]), ha="center", va="center",
                    color="white" if M[i, j] > M.max() / 2 else "black")
    fig.colorbar(im, ax=ax, label="ads")
    ax.set_title("Brand × cluster counts")
    png = save_fig(fig, Path(out_dir) / "distributions" / "brand_by_cluster.png")
    write_csv(Path(out_dir) / "distributions" / "brand_by_cluster_table.csv",
              [{"brand": b, **{cluster_label(c): int(M[i, j]) for j, c in enumerate(clusters)}}
               for i, b in enumerate(brands)])
    mp = write_csv(Path(out_dir) / "distributions" / "brand_by_cluster.csv",
                   [{"ad_id": a, "brand": inp.brands[a], "cluster": cluster_label(inp.clusters[a])} for a in inp.ad_ids])
    return manifest.add(png, "brand_cluster", "Counts of ads per brand and cluster (table in brand_by_cluster_table.csv)",
                        covered=inp.ad_ids, mapping=mp)


def _groups(inp: AnalyticsInput, ads: List[str]) -> List[Tuple[str, List[str]]]:
    g = [(f"brand: {b}", [a for a in ads if inp.brands[a] == b]) for b in inp.ordered_brands]
    g += [(f"cluster: {cluster_label(c)}", [a for a in ads if inp.clusters[a] == c]) for c in inp.ordered_clusters]
    return [(n, m) for n, m in g if m]


def dominant_colour_strips(inp: AnalyticsInput, out_dir: Path, manifest: Manifest) -> dict:
    """Each group is one horizontal strip; each ad gets 1/n of the width, split by its own
    dominant-colour proportions. Nothing is re-binned, so the strip shows the actual colours."""
    plt = setup_matplotlib()
    ok, missing = _split(inp, "dominant_colours", lambda v: isinstance(v, list) and len(v) > 0)
    groups = _groups(inp, ok)
    fig, ax = plt.subplots(figsize=(11, 0.45 * len(groups) + 1.2))
    rows = []
    for gi, (name, members) in enumerate(groups):
        w = 1.0 / len(members)
        x = 0.0
        for a in sorted(members):
            cols = _field(inp, a, "dominant_colours")
            tot = sum(c["proportion"] for c in cols) or 1.0
            for c in cols:
                cw = w * c["proportion"] / tot
                ax.barh(gi, cw, left=x, color=c["hex"], height=0.8, edgecolor="none")
                rows.append({"group": name, "ad_id": a, "brand": inp.brands[a], "hex": c["hex"],
                             "proportion": c["proportion"], "x_start": round(x, 6), "x_end": round(x + cw, 6)})
                x += cw
    ax.set_yticks(range(len(groups)), [g[0] for g in groups])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of group (each ad = equal width, split by its k-means colour proportions)")
    ax.set_title("Dominant colours by brand and cluster")
    png = save_fig(fig, Path(out_dir) / "distributions" / "dominant_colours.png")
    mp = write_csv(Path(out_dir) / "distributions" / "dominant_colours.csv", rows)
    return manifest.add(png, "dominant_colours", "Dominant colour strips per brand and per cluster",
                        covered=ok, missing=missing, mapping=mp)


def orientation_aspect(inp: AnalyticsInput, out_dir: Path, manifest: Manifest) -> dict:
    plt = setup_matplotlib()
    ok, missing = _split(inp, "aspect_ratio", lambda v: isinstance(v, (int, float)) and v > 0)
    brands = [b for b in inp.ordered_brands if any(inp.brands[a] == b for a in ok)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 0.5 * len(brands) + 2.5))
    left = np.zeros(len(brands))
    for oi, o in enumerate(ORIENTATIONS):
        vals = np.array([sum(1 for a in ok if inp.brands[a] == b and _field(inp, a, "orientation") == o)
                         for b in brands])
        a1.barh(brands, vals, left=left, color=OKABE_ITO[oi], label=o)
        left += vals
    a1.legend(frameon=False)
    a1.set_xlabel("ads")
    a1.set_title("Orientation by brand")
    rng = np.random.default_rng(0)
    rows = []
    for bi, b in enumerate(brands):
        ads = sorted(a for a in ok if inp.brands[a] == b)
        jit = rng.uniform(-0.18, 0.18, len(ads))
        xs = [float(_field(inp, a, "aspect_ratio")) for a in ads]
        a2.scatter(xs, bi + jit, s=40, color=OKABE_ITO[4], alpha=0.8)
        rows += [{"ad_id": a, "brand": b, "orientation": _field(inp, a, "orientation"), "aspect_ratio": x,
                  "y": round(float(bi + j), 4)} for a, x, j in zip(ads, xs, jit)]
    for ref, lab in ((1.0, "1:1"), (0.8, "4:5"), (0.5625, "9:16"), (1.91, "1.91:1")):
        a2.axvline(ref, color="#BBBBBB", lw=0.8, ls="--")
        a2.text(ref, len(brands) - 0.4, lab, fontsize=8, color="#666666", ha="center")
    a2.set_yticks(range(len(brands)), brands)
    a2.set_xlabel("aspect ratio (width / height)")
    a2.set_title("Aspect ratio per ad")
    png = save_fig(fig, Path(out_dir) / "distributions" / "orientation_aspect.png")
    mp = write_csv(Path(out_dir) / "distributions" / "orientation_aspect.csv", rows)
    return manifest.add(png, "orientation_aspect", "Orientation counts and per-ad aspect ratios by brand",
                        covered=ok, missing=missing, mapping=mp)


def text_density_chart(inp: AnalyticsInput, out_dir: Path, manifest: Manifest) -> dict:
    plt = setup_matplotlib()
    ok, missing = _split(inp, "text_density", lambda v: isinstance(v, (int, float)))
    groups = _groups(inp, ok)
    fig, ax = plt.subplots(figsize=(11, 0.45 * len(groups) + 1.5))
    rng = np.random.default_rng(0)
    rows = []
    data = [[float(_field(inp, a, "text_density")) for a in sorted(m)] for _, m in groups]
    if groups:
        kw = dict(positions=range(len(groups)), widths=0.6, showfliers=False, medianprops={"color": "#D55E00"})
        try:  # matplotlib >= 3.10
            ax.boxplot(data, orientation="horizontal", **kw)
        except TypeError:
            ax.boxplot(data, vert=False, **kw)
    for gi, (name, members) in enumerate(groups):
        ads = sorted(members)
        jit = rng.uniform(-0.2, 0.2, len(ads))
        ax.scatter(data[gi], gi + jit, s=18, color="#0072B2", alpha=0.75, zorder=3)
        rows += [{"group": name, "ad_id": a, "brand": inp.brands[a], "text_density": v, "y": round(float(gi + j), 4)}
                 for a, v, j in zip(ads, data[gi], jit)]
    ax.set_yticks(range(len(groups)), [g[0] for g in groups])
    ax.invert_yaxis()
    ax.set_xlabel("OCR text density (share of image area covered by text boxes)")
    ax.set_title("Text density by brand and cluster (each dot = one ad)")
    png = save_fig(fig, Path(out_dir) / "distributions" / "text_density.png")
    mp = write_csv(Path(out_dir) / "distributions" / "text_density.csv", rows)
    return manifest.add(png, "text_density", "OCR text-density box + per-ad dots, per brand and per cluster",
                        covered=ok, missing=missing, mapping=mp)


def layout_chart(inp: AnalyticsInput, out_dir: Path, manifest: Manifest) -> dict:
    plt = setup_matplotlib()
    ok, missing = _split(inp, "layout_category", lambda v: isinstance(v, str) and v != "")
    groups = _groups(inp, ok)
    cats = LAYOUTS + sorted({_field(inp, a, "layout_category") for a in ok} - set(LAYOUTS))
    fig, ax = plt.subplots(figsize=(11, 0.45 * len(groups) + 1.5))
    left = np.zeros(len(groups))
    for ci, cat in enumerate(cats):
        vals = np.array([sum(1 for a in m if _field(inp, a, "layout_category") == cat) for _, m in groups])
        if vals.sum():
            ax.barh(range(len(groups)), vals, left=left,
                    color=NOISE_COLOUR if cat == "unknown" else (OKABE_ITO[ci % 8]), label=cat)
            left += vals
    ax.set_yticks(range(len(groups)), [g[0] for g in groups])
    ax.invert_yaxis()
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1))
    ax.set_xlabel("ads")
    ax.set_title("Rule-based layout category by brand and cluster (heuristic labels)")
    png = save_fig(fig, Path(out_dir) / "distributions" / "layout_categories.png")
    mp = write_csv(Path(out_dir) / "distributions" / "layout_categories.csv",
                   [{"ad_id": a, "brand": inp.brands[a], "cluster": cluster_label(inp.clusters[a]),
                     "layout_category": _field(inp, a, "layout_category")} for a in ok])
    return manifest.add(png, "layout_category", "Layout category counts per brand and per cluster",
                        covered=ok, missing=missing, mapping=mp,
                        extra={"counts": dict(Counter(_field(inp, a, "layout_category") for a in ok))})

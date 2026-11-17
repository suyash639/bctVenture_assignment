"""
generate_all: produce every visual-analytics artefact plus manifest.json.

    from src.analytics import generate_all
    manifest = generate_all(bundle, fm, "data/outputs/clustering/assignments.csv",
                            out_dir="data/outputs/analytics", base_dir=".")

Raises CoverageError if any artefact would silently omit an input ad_id.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

from src.analytics.common import Manifest, cluster_label, normalise_inputs, write_csv, write_json
from src.analytics.contact_sheets import cluster_contact_sheets
from src.analytics.distributions import (
    brand_cluster_matrix,
    cluster_size_chart,
    dominant_colour_strips,
    layout_chart,
    orientation_aspect,
    text_density_chart,
)
from src.analytics.projections import projection_plots
from src.analytics.representatives import representative_rows, select_representatives


def generate_all(bundle, fm, assignments: Union[str, Path, Sequence[dict]], out_dir="data/outputs/analytics",
                 base_dir=".", k_representatives: int = 3, seed: int = 0) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    inp = normalise_inputs(bundle, assignments)
    man = Manifest(inp.ad_ids, out)

    reps = select_representatives(inp, fm, k_representatives)
    write_json(out / "representatives.json", reps)
    rp = write_csv(out / "representatives.csv", representative_rows(reps),
                   ["cluster", "rank", "ad_id", "brand", "distance_to_centroid"])
    rep_ids = [r["ad_id"] for v in reps.values() for r in v["representatives"]]
    man.add(rp, "representatives", f"Top-{k_representatives} ads closest to each cluster centroid in fm.X",
            covered=rep_ids,
            missing=[{"ad_id": a, "reason": ("noise / unassigned: no centroid" if inp.clusters[a] in (None, -1)
                                             else "cluster member, not among closest-to-centroid")}
                     for a in inp.ad_ids if a not in rep_ids])

    cluster_contact_sheets(inp, out, man, base_dir, reps)
    projection_plots(inp, fm, out, man, seed)
    cluster_size_chart(inp, out, man)
    brand_cluster_matrix(inp, out, man)
    dominant_colour_strips(inp, out, man)
    orientation_aspect(inp, out, man)
    text_density_chart(inp, out, man)
    layout_chart(inp, out, man)

    failures = sorted({f["ad_id"] for e in man.entries for f in e.get("image_load_failures", [])})
    return man.write(seed=seed, k_representatives=k_representatives,
                     clusters={cluster_label(c): len(inp.members(c)) for c in inp.ordered_clusters},
                     image_load_failures=failures, assignment_issues=inp.assignment_issues)

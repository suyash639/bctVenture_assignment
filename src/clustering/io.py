"""Writers for clustering outputs (contract: docs/analysis_data_contract.md)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Optional

from src.clustering.core import ClusteringResult, to_json
from src.clustering.evaluation import Selection, SweepResult

ASSIGNMENT_COLUMNS = ["ad_id", "brand", "cluster_id", "is_noise", "algorithm", "config_id",
                      "distance_to_centroid", "membership_probability"]


def write_assignments(result: ClusteringResult, path, brands: Optional[Dict[str, Optional[str]]] = None) -> Path:
    rows = result.to_assignments(brands)
    if len(rows) != len(result.ad_ids) or len({r["ad_id"] for r in rows}) != len(rows):
        raise AssertionError("assignments must contain exactly one row per input ad_id")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ASSIGNMENT_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return p


def read_assignments(path) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["cluster_id"] = int(r["cluster_id"])
        r["is_noise"] = r["is_noise"] == "True"
    return rows


def write_sweep(sweep: SweepResult, path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(to_json(sweep.to_dict()))
    return p


def write_selection(selection: Selection, path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(to_json(selection.to_dict()))
    return p


def write_all(sweep: SweepResult, selection: Selection, out_dir="data/outputs/clustering") -> Dict[str, Path]:
    """sweep_results.json, selected_configuration.json and assignments.csv for the selected config."""
    out = Path(out_dir)
    paths = {"sweep": write_sweep(sweep, out / "sweep_results.json"),
             "selection": write_selection(selection, out / "selected_configuration.json")}
    if selection.config is not None:
        entry = sweep.get(selection.config.config_id)
        paths["assignments"] = write_assignments(entry.result, out / "assignments.csv", sweep.brands)
    return paths

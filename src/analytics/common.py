"""
Shared helpers for src/analytics: input normalisation, the artefact manifest (with
coverage enforcement), palette and small I/O utilities.

Inputs are duck-typed (see docs/analysis_data_contract.md):
  bundle       .ad_ids (list[str]), .records {ad_id: feature record (+ record["dataset"])}
  fm           .X (m, k) ndarray, .ad_ids (list[str], row-aligned)
  assignments  list[dict] or path to assignments.csv (ad_id, cluster_id, is_noise, brand, ...)

Coverage rule: every artefact must account for every input ad_id, either as covered
(drawn / tabulated) or as missing with an explicit reason. Manifest.add() raises if not.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Union

NOISE = -1
UNASSIGNED = None  # ad present in the bundle but absent from assignments

# Okabe-Ito (colour-blind safe), then a muted extension for >8 clusters.
OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]
EXTENSION = ["#999933", "#882255", "#44AA99", "#117733", "#332288", "#AA4499", "#88CCEE", "#DDCC77",
             "#661100", "#6699CC", "#AA4466", "#4477AA"]
NOISE_COLOUR = "#9E9E9E"
UNASSIGNED_COLOUR = "#D9D9D9"
BRAND_MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*", "h", "<", ">"]


class CoverageError(AssertionError):
    """An artefact neither covered nor explained some input ad_ids."""


def cluster_colour(cluster_id: Optional[int], ordered_clusters: Sequence[int]) -> str:
    if cluster_id is None:
        return UNASSIGNED_COLOUR
    if cluster_id == NOISE:
        return NOISE_COLOUR
    real = [c for c in ordered_clusters if c not in (None, NOISE)]
    pal = OKABE_ITO + EXTENSION
    return pal[real.index(cluster_id) % len(pal)]


def cluster_label(cluster_id: Optional[int]) -> str:
    if cluster_id is None:
        return "unassigned"
    return "noise" if cluster_id == NOISE else f"C{cluster_id}"


# --------------------------------------------------------------------------- inputs

def _as_int(v) -> Optional[int]:
    if v is None or v == "":
        return None
    return int(float(v))


def _truthy(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "t")


def load_assignments(assignments: Union[str, Path, Sequence[dict]]) -> Dict[str, dict]:
    """ad_id -> {"cluster_id": int (-1 noise), "is_noise": bool, ...original columns}."""
    if isinstance(assignments, (str, Path)):
        with open(assignments, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        rows = [dict(r) for r in assignments]
    out: Dict[str, dict] = {}
    for r in rows:
        ad = str(r["ad_id"])
        if ad in out:
            raise ValueError(f"duplicate ad_id in assignments: {ad}")
        cid = _as_int(r.get("cluster_id"))
        noise = _truthy(r.get("is_noise")) if r.get("is_noise") not in (None, "") else cid == NOISE
        if noise:
            cid = NOISE
        out[ad] = {**r, "ad_id": ad, "cluster_id": cid, "is_noise": noise}
    return out


@dataclass
class AnalyticsInput:
    """Normalised view used by every analytics function."""
    ad_ids: List[str]                       # universe, bundle order
    records: Dict[str, dict]
    clusters: Dict[str, Optional[int]]      # ad_id -> cluster id / -1 noise / None unassigned
    brands: Dict[str, str]
    assignment_issues: List[dict] = field(default_factory=list)

    @property
    def ordered_clusters(self) -> List[Optional[int]]:
        cs = sorted({c for c in self.clusters.values() if c not in (None, NOISE)})
        if any(c == NOISE for c in self.clusters.values()):
            cs.append(NOISE)
        if any(c is None for c in self.clusters.values()):
            cs.append(None)
        return cs

    @property
    def ordered_brands(self) -> List[str]:
        return sorted(set(self.brands.values()))

    def members(self, cluster_id) -> List[str]:
        return [a for a in self.ad_ids if self.clusters[a] == cluster_id]


def normalise_inputs(bundle, assignments) -> AnalyticsInput:
    ad_ids = [str(a) for a in bundle.ad_ids]
    if len(ad_ids) != len(set(ad_ids)):
        raise ValueError("duplicate ad_ids in bundle")
    records = {str(k): v for k, v in bundle.records.items()}
    amap = load_assignments(assignments) if assignments is not None else {}
    issues = [{"ad_id": a, "problem": "assignment for ad_id not in feature bundle"}
              for a in amap if a not in records]
    clusters = {a: (amap[a]["cluster_id"] if a in amap else UNASSIGNED) for a in ad_ids}
    brands = {}
    for a in ad_ids:
        rec = records.get(a, {})
        b = rec.get("brand") or (rec.get("dataset") or {}).get("brand") or (amap.get(a) or {}).get("brand")
        brands[a] = b or "unknown"
    return AnalyticsInput(ad_ids, records, clusters, brands, issues)


def image_path_of(record: dict, base_dir: Union[str, Path]) -> Optional[Path]:
    p = record.get("image_path") or (record.get("dataset") or {}).get("local_image_path")
    if not p:
        return None
    p = Path(p)
    return p if p.is_absolute() else Path(base_dir) / p


# --------------------------------------------------------------------------- manifest

class Manifest:
    def __init__(self, universe: Sequence[str], out_dir: Union[str, Path]):
        self.universe = list(universe)
        self.out_dir = Path(out_dir)
        self.entries: List[dict] = []

    def _rel(self, p: Union[str, Path]) -> str:
        p = Path(p)
        try:
            return str(p.relative_to(self.out_dir))
        except ValueError:
            return str(p)

    def add(self, path, kind: str, description: str, covered: Iterable[str],
            missing: Optional[List[dict]] = None, mapping: Optional[Union[str, Path]] = None,
            status: str = "ok", extra: Optional[dict] = None) -> dict:
        covered = list(dict.fromkeys(covered))
        missing = list(missing or [])
        accounted = set(covered) | {m["ad_id"] for m in missing}
        lost = [a for a in self.universe if a not in accounted]
        if lost:
            raise CoverageError(f"{path}: {len(lost)} ad_ids neither covered nor explained: {lost[:5]}")
        overlap = set(covered) & {m["ad_id"] for m in missing}
        if overlap:
            raise CoverageError(f"{path}: ad_ids both covered and missing: {sorted(overlap)[:5]}")
        e = {"path": self._rel(path) if path else None, "kind": kind, "description": description,
             "status": status, "mapping": self._rel(mapping) if mapping else None,
             "n_records": len(self.universe), "n_covered": len(covered),
             "ad_ids_covered": covered, "n_missing_with_reasons": len(missing), "missing": missing}
        if extra:
            e.update(extra)
        self.entries.append(e)
        return e

    def to_dict(self, **summary) -> dict:
        return {"n_input_ad_ids": len(self.universe), "n_artefacts": len(self.entries),
                **summary, "artefacts": self.entries}

    def write(self, **summary) -> dict:
        d = self.to_dict(**summary)
        (self.out_dir / "manifest.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
        return d


# --------------------------------------------------------------------------- io

def write_csv(path: Union[str, Path], rows: List[dict], cols: Optional[List[str]] = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = cols or (list(rows[0].keys()) if rows else ["ad_id"])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path


def write_json(path: Union[str, Path], obj) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    return path


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
                         "figure.dpi": 110, "savefig.dpi": 110, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.hashsalt": "advision"})
    return plt


def save_fig(fig, path: Union[str, Path]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", metadata={"Software": None})
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path

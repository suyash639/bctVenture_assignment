"""
Load and validate the outputs of src/vision/feature_pipeline.py into a FeatureBundle.

Validation (hard errors raise; soft problems go to `issues`; dropped records go to `excluded`):
  * ad_id must be a str and unique across feature records          -> raise
  * embedding rows must agree two ways: meta.clip.row_ad_ids[row] == ad_id for every record's
    clip_embedding_reference, and every row_ad_id has exactly one referencing record -> raise
  * .npy must be 2-D with n_rows == len(row_ad_ids)                 -> raise
  * non-finite embedding                                           -> issue + NaN row
  * L2 norm: |n-1| <= 1e-4 ok; <= 1e-3 re-normalised + issue; else issue + NaN row
  * extraction_status == "failed"                                  -> excluded
  * missing numeric fields                                         -> issue (imputed/dropped later)
  * optional dataset join on ad_id with a required-status filter: features without a dataset
    row, rows failing the filter, and filter-passing dataset rows without features -> excluded
Nothing is dropped silently.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

NORM_OK = 1e-4
NORM_FIX = 1e-3
NUMERIC_FIELDS = ["aspect_ratio", "brightness", "contrast", "sharpness", "colourfulness",
                  "text_density", "ocr_n_text_regions"]


class AlignmentError(ValueError):
    """Embedding rows, record references and ad_ids disagree."""


@dataclass
class FeatureBundle:
    ad_ids: List[str]
    records: Dict[str, dict]
    embeddings: np.ndarray                # (n, d) row-aligned to ad_ids; NaN rows = unavailable
    issues: List[dict] = field(default_factory=list)
    excluded: List[tuple] = field(default_factory=list)   # (ad_id, reason)
    meta: dict = field(default_factory=dict)

    @property
    def embedding_dim(self) -> int:
        return int(self.embeddings.shape[1])

    def has_embedding(self, ad_id: str) -> bool:
        return bool(np.all(np.isfinite(self.embeddings[self.ad_ids.index(ad_id)])))


def _read_dataset(path: Path) -> Dict[str, dict]:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        with open(p, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        d = json.loads(p.read_text(encoding="utf-8"))
        rows = d.get("ads", d.get("records", [])) if isinstance(d, dict) else d
    out = {}
    for r in rows:
        aid = str(r["ad_id"])
        if aid in out:
            raise AlignmentError(f"duplicate ad_id {aid} in dataset {p}")
        out[aid] = r
    return out


def load_feature_bundle(features_json, embeddings_npy, dataset_csv=None,
                        require_dataset_status: Optional[Dict[str, str]] = None) -> FeatureBundle:
    data = json.loads(Path(features_json).read_text(encoding="utf-8"))
    meta, recs = data.get("meta", {}), data.get("records", [])
    issues: List[dict] = []
    excluded: List[tuple] = []

    # --- ids
    seen = set()
    for r in recs:
        aid = r.get("ad_id")
        if not isinstance(aid, str) or not aid:
            raise AlignmentError(f"ad_id must be a non-empty str, got {aid!r} ({type(aid).__name__})")
        if aid in seen:
            raise AlignmentError(f"duplicate ad_id {aid} in {features_json}")
        seen.add(aid)

    # --- embeddings and two-way alignment
    emb_path = Path(embeddings_npy)
    emb = np.load(emb_path) if emb_path.exists() else np.zeros((0, 0), np.float32)
    if emb.ndim != 2:
        raise AlignmentError(f"embeddings must be 2-D, got shape {emb.shape}")
    row_ids = [str(x) for x in (meta.get("clip") or {}).get("row_ad_ids", [])]
    if emb.shape[0] != len(row_ids):
        raise AlignmentError(f"npy has {emb.shape[0]} rows but meta.clip.row_ad_ids has {len(row_ids)}")
    if len(set(row_ids)) != len(row_ids):
        raise AlignmentError("meta.clip.row_ad_ids contains duplicates")
    ref_rows = {}
    for r in recs:
        ref = r.get("clip_embedding_reference")
        if ref is None:
            continue
        row = ref.get("row")
        if not isinstance(row, int) or not 0 <= row < len(row_ids):
            raise AlignmentError(f"{r['ad_id']}: clip_embedding_reference row {row!r} out of range")
        if row_ids[row] != r["ad_id"]:
            raise AlignmentError(f"{r['ad_id']}: reference row {row} belongs to {row_ids[row]} in meta.clip.row_ad_ids")
        ref_rows[r["ad_id"]] = row
    unreferenced = set(row_ids) - set(ref_rows)
    if unreferenced:
        raise AlignmentError(f"embedding rows without a referencing record: {sorted(unreferenced)}")
    dim = emb.shape[1] if emb.shape[0] else int((meta.get("clip") or {}).get("embedding_dim") or 0)

    # --- dataset join
    ds = _read_dataset(dataset_csv) if dataset_csv else None

    ad_ids, records, rows = [], {}, []
    for r in recs:
        aid = r["ad_id"]
        if r.get("extraction_status") == "failed":
            excluded.append((aid, f"feature extraction failed: {r.get('extraction_error')}"))
            continue
        rec = dict(r)
        if ds is not None:
            drow = ds.get(aid)
            if drow is None:
                excluded.append((aid, "not present in dataset"))
                continue
            bad = {k: drow.get(k) for k, v in (require_dataset_status or {}).items() if drow.get(k) != v}
            if bad:
                excluded.append((aid, "dataset filter not met: " + ", ".join(f"{k}={v}" for k, v in bad.items())))
                continue
            rec["dataset"] = drow
        for f in NUMERIC_FIELDS:
            v = r.get(f)
            if v is None or (isinstance(v, float) and not np.isfinite(v)):
                issues.append({"ad_id": aid, "field": f, "problem": "missing"})
        if r.get("extraction_status") == "partial":
            issues.append({"ad_id": aid, "field": "extraction_status",
                           "problem": f"partial: {r.get('extraction_error')}"})
        vec = np.full(dim, np.nan, np.float32)
        if aid in ref_rows:
            v = emb[ref_rows[aid]].astype(np.float64)
            if not np.all(np.isfinite(v)):
                issues.append({"ad_id": aid, "field": "clip_embedding", "problem": "non-finite values"})
            else:
                n = float(np.linalg.norm(v))
                if abs(n - 1) <= NORM_OK:
                    vec = v.astype(np.float32)
                elif abs(n - 1) <= NORM_FIX:
                    vec = (v / n).astype(np.float32)
                    issues.append({"ad_id": aid, "field": "clip_embedding", "problem": f"norm {n:.6f}; re-normalised"})
                else:
                    issues.append({"ad_id": aid, "field": "clip_embedding",
                                   "problem": f"norm {n:.6f} not ~1; embedding marked unavailable"})
        else:
            issues.append({"ad_id": aid, "field": "clip_embedding", "problem": "no embedding reference"})
        ad_ids.append(aid)
        records[aid] = rec
        rows.append(vec)

    if ds is not None and require_dataset_status is not None:
        feat_ids = {r["ad_id"] for r in recs}
        for aid, drow in ds.items():
            if aid not in feat_ids and all(drow.get(k) == v for k, v in require_dataset_status.items()):
                excluded.append((aid, "passes dataset filter but has no feature record"))

    E = np.stack(rows) if rows else np.zeros((0, dim), np.float32)
    return FeatureBundle(ad_ids=ad_ids, records=records, embeddings=E, issues=issues, excluded=excluded,
                         meta={"features_json": str(features_json), "embeddings_npy": str(embeddings_npy),
                               "dataset": str(dataset_csv) if dataset_csv else None,
                               "require_dataset_status": require_dataset_status,
                               "vision_meta": meta, "embedding_dim": dim})

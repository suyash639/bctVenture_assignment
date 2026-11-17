"""
Write reports/feature_extraction_report.md from the real feature-extraction outputs
(data/processed/visual_features.json + clip_embeddings.npy) and their validation.

Usage: python scripts/generate_feature_report.py
"""
from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.vision.feature_pipeline import validate_outputs  # noqa: E402

FJ = ROOT / "data/processed/visual_features.json"
NPY = ROOT / "data/processed/clip_embeddings.npy"
DS = ROOT / "data/processed/validated_dataset.csv"
OUT = ROOT / "reports/feature_extraction_report.md"


def q(vals):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return "—"
    return f"median {st.median(v):.3f} (min {v[0]:.3f}, max {v[-1]:.3f}, n={len(v)})"


def table(h, rows):
    return "\n".join(["| " + " | ".join(h) + " |", "|" + "---|" * len(h)] +
                     ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def main():
    data = json.loads(FJ.read_text())
    meta, recs = data["meta"], data["records"]
    emb = np.load(NPY)
    val = validate_outputs(FJ, NPY, DS)
    norms = np.linalg.norm(emb, axis=1) if len(emb) else np.array([])
    brands = sorted({r["brand"] for r in recs})
    lines = [
        "# Feature Extraction Report", "",
        f"Generated from `{FJ.relative_to(ROOT)}` (created {meta.get('created_at')}) by `scripts/generate_feature_report.py`.", "",
        "## Run", "",
        f"- Input selection: {json.dumps(meta.get('selection', {}).get('requirements'))} from "
        f"`{meta.get('selection', {}).get('dataset')}` (sha256 `{str(meta.get('selection', {}).get('dataset_sha256'))[:12]}`)",
        f"- Records: **{len(recs)}**; status {meta.get('status_counts')}",
        f"- CLIP: {meta['clip'].get('model')} on `{meta['clip'].get('device')}`, dim {meta['clip'].get('embedding_dim')}, "
        f"{meta['clip'].get('n_embedded')} embedded; OCR: {meta['ocr'].get('backend')} ({meta['ocr'].get('status')})",
        f"- Elapsed: {meta.get('elapsed_seconds')} s", "",
        "## Validation (`src.vision.feature_pipeline --validate`)", "",
        table(["Check", "Result"], [[k, "PASS" if v else "**FAIL**"] for k, v in val["checks"].items()]), "",
        f"Overall: **{'PASSED' if val['ok'] else 'FAILED'}**. Embedding L2 norms: min {norms.min():.6f}, max {norms.max():.6f}. "
        f"Failed records: {val.get('failed_records') or 'none'}; partial: {val.get('partial_records') or 'none'}.", "",
        "## Feature summary by brand", "",
        table(["Brand", "n", "orientation", "text density", "sharpness", "colourfulness", "layout labels"],
              [[b, sum(r['brand'] == b for r in recs),
                dict(Counter(r["orientation"] for r in recs if r["brand"] == b)),
                q([r["text_density"] for r in recs if r["brand"] == b]),
                q([r["sharpness"] for r in recs if r["brand"] == b]),
                q([r["colourfulness"] for r in recs if r["brand"] == b]),
                dict(Counter(r["layout_category"] for r in recs if r["brand"] == b))] for b in brands]), "",
        "## OCR coverage", "",
        f"- Creatives with ≥ 1 detected text region: {sum(1 for r in recs if (r.get('ocr_n_text_regions') or 0) > 0)}/{len(recs)}",
        f"- Detected regions: {sum(r.get('ocr_n_text_regions') or 0 for r in recs)}; readable (conf ≥ "
        f"{meta['ocr'].get('min_confidence')}): {sum(r.get('ocr_n_readable_regions') or 0 for r in recs)}", "",
        "## Notes", "",
        "- Layout labels are rule-based heuristics (`src/vision/layout_classifier.py`) and have not been "
        "validated against human labels.",
        "- Devanagari text is detected (it counts toward text density) but mostly not transcribed; ₹ is often dropped.",
        "- These are features, not findings. Clustering and observations are produced by `make analyze`.", "",
    ]
    OUT.write_text("\n".join(lines))
    print(OUT, "validation ok:", val["ok"])
    return 0 if val["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

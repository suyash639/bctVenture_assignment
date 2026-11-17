"""
Unified visual feature extraction pipeline.

    # extract (only rows meeting every --require condition)
    python -m src.vision.feature_pipeline --dataset data/processed/validated_dataset.csv \
        --require final_status=VERIFIED

    # validate existing outputs (exit code 1 on any failed check)
    python -m src.vision.feature_pipeline --validate --dataset data/processed/validated_dataset.csv

Writes
  <out-json>  {"meta": {...}, "records": [one record per input ad]}
  <out-npy>   float32 (N_embedded, D) L2-normalised CLIP image embeddings; each record's
              clip_embedding_reference = {"file": ..., "row": i} (null if not embedded).

Stages run per batch so memory stays bounded by --batch-size. A failure in one stage
(e.g. OCR or CLIP unavailable) is recorded in extraction_error and the record is marked
"partial"; an unreadable image is marked "failed". Nothing is invented for failed stages.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import BASE_DIR, VISION_CONFIG  # noqa: E402
from src.vision.image_features import extract_image_properties  # noqa: E402
from src.vision.layout_classifier import VISUAL_PROMPTS, classify_layout  # noqa: E402
from src.vision.preprocessing import (  # noqa: E402
    ImageRecord,
    check_unique_ad_ids,
    iter_loaded,
    parse_requirements,
    records_from_directory,
    select_from_dataset,
)

SCHEMA_VERSION = "1.0"
NULL_IMAGE = {"width": None, "height": None, "aspect_ratio": None, "orientation": None,
              "brightness": None, "contrast": None, "sharpness": None, "colourfulness": None,
              "dominant_colours": None, "colour_distribution": None}
NULL_OCR = {"ocr_text": None, "ocr_n_text_regions": None, "ocr_n_readable_regions": None,
            "ocr_mean_confidence": None, "text_density": None, "text_position": None,
            "text_position_distribution": None}


def _rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(BASE_DIR))
    except ValueError:
        return str(p)


def run(records: List[ImageRecord], out_json: Path, out_npy: Path, use_clip: bool = True,
        use_ocr: bool = True, batch_size: Optional[int] = None, device: Optional[str] = None,
        clip_model: Optional[str] = None, clip_pretrained: Optional[str] = None,
        verbose: bool = True, selection: Optional[Dict] = None) -> Dict:
    C = VISION_CONFIG
    check_unique_ad_ids(records)  # fail fast: one ad -> one record -> at most one embedding row
    batch_size = batch_size or C["clip_batch_size"]
    t0 = time.time()

    ocr = clip = None
    ocr_status = clip_status = "disabled"
    if use_ocr:
        from src.vision.ocr_features import OcrUnavailableError, RapidOcrBackend
        try:
            ocr = RapidOcrBackend().load()
            ocr_status = "ok"
        except OcrUnavailableError as e:
            ocr_status = f"unavailable: {e}"
    if use_clip:
        from src.vision.clip_embeddings import ClipEmbedder, ClipUnavailableError
        try:
            clip = ClipEmbedder(clip_model, clip_pretrained, device, batch_size).load()
            prompt_keys = list(VISUAL_PROMPTS)
            prompt_texts = [VISUAL_PROMPTS[k][1] for k in prompt_keys]
            clip_status = "ok"
        except ClipUnavailableError as e:
            clip_status = f"unavailable: {e}"

    out_records: List[Dict] = []
    embeddings: List[np.ndarray] = []
    for start in range(0, len(records), batch_size):
        chunk = list(iter_loaded(records[start:start + batch_size]))
        loaded = []
        for rec, img, err in chunk:
            r = {"ad_id": rec.ad_id, "brand": rec.brand,
                 "image_path": rec.extra.get("image_path_raw") or _rel(rec.image_path),
                 **NULL_IMAGE, "clip_embedding_reference": None, **NULL_OCR,
                 "layout_category": None, "layout_reasons": None, "layout_scores": None,
                 "extraction_status": None, "extraction_error": None}
            errors = []
            if img is None:
                r["extraction_status"], r["extraction_error"] = "failed", err
                out_records.append(r)
                continue
            try:
                r.update(extract_image_properties(img.rgb, C["analysis_max_side"],
                                                  C["sharpness_short_side"], C["n_dominant_colours"]))
            except Exception as e:
                errors.append(f"image_properties: {e}")
            if ocr is not None:
                try:
                    from src.vision.ocr_features import text_features
                    boxes = ocr.detect(img.rgb)
                    r.update(text_features(boxes, img.rgb.width, img.rgb.height, C["ocr_min_confidence"]))
                except Exception as e:
                    errors.append(f"ocr: {e}")
            elif use_ocr:
                errors.append(f"ocr {ocr_status}")
            r["_errors"] = errors
            out_records.append(r)
            loaded.append((r, img))

        zero_shot_by_id = {}
        if clip is not None and loaded:
            try:
                emb = clip.embed_images([img.rgb for _, img in loaded])
                probs = clip.zero_shot(emb, prompt_texts)
                for (r, _), e, p in zip(loaded, emb, probs):
                    r["clip_embedding_reference"] = {"file": _rel(out_npy), "row": len(embeddings)}
                    embeddings.append(e)
                    zero_shot_by_id[id(r)] = {k: round(float(v), 4) for k, v in zip(prompt_keys, p)}
            except Exception as e:
                for r, _ in loaded:
                    r["_errors"].append(f"clip: {e}")
        elif use_clip:
            for r, _ in loaded:
                r["_errors"].append(f"clip {clip_status}")

        for r, _ in loaded:
            r.update(classify_layout(r["ocr_text"], r["text_density"], r["ocr_n_text_regions"],
                                     zero_shot_by_id.get(id(r))))
            errs = r.pop("_errors")
            r["extraction_status"] = "partial" if errs else "success"
            r["extraction_error"] = "; ".join(errs) or None
        if verbose:
            print(f"  processed {min(start + batch_size, len(records))}/{len(records)}", flush=True)

    dim = int(embeddings[0].shape[0]) if embeddings else (clip.dim if clip else 0)
    emb_arr = np.stack(embeddings).astype(np.float32) if embeddings else np.zeros((0, dim), np.float32)
    meta = {
        "schema_version": SCHEMA_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "n_input_records": len(records),
        "selection": selection or {"source": "explicit record list", "n_selected": len(records)},
        "status_counts": {s: sum(r["extraction_status"] == s for r in out_records)
                          for s in ("success", "partial", "failed")},
        "clip": {"status": clip_status, "model": clip.model_id if clip else None,
                 "device": clip.device if clip else None, "embedding_dim": dim,
                 "n_embedded": int(emb_arr.shape[0]), "normalised": "L2",
                 "file": _rel(out_npy), "row_ad_ids": [r["ad_id"] for r in out_records
                                                       if r["clip_embedding_reference"]]},
        "ocr": {"status": ocr_status, "backend": "rapidocr_onnxruntime" if ocr else None,
                "min_confidence": C["ocr_min_confidence"]},
        "image_properties": {"analysis_max_side": C["analysis_max_side"],
                             "sharpness_short_side": C["sharpness_short_side"]},
        "layout": {"method": "rule-based (src/vision/layout_classifier.py)",
                   "visual_prompts": {k: v[1] for k, v in VISUAL_PROMPTS.items()}},
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    tmp_json, tmp_npy = out_json.with_suffix(".json.tmp"), out_npy.with_suffix(".tmp.npy")
    np.save(tmp_npy, emb_arr)
    tmp_json.write_text(json.dumps({"meta": meta, "records": out_records}, indent=1, ensure_ascii=False))
    os.replace(tmp_npy, out_npy)
    os.replace(tmp_json, out_json)
    if verbose:
        print(f"wrote {_rel(out_json)} ({len(out_records)} records) and {_rel(out_npy)} {emb_arr.shape}")
        print(f"status: {meta['status_counts']}  clip: {clip_status}  ocr: {ocr_status}")
    return {"meta": meta, "records": out_records}


def validate_outputs(json_path: Path, npy_path: Path, dataset_path: Optional[Path] = None,
                     requirements: Optional[Dict[str, List[str]]] = None, base_dir: Path = BASE_DIR) -> Dict:
    """
    Check a finished run. Returns {"ok", "checks", "errors", "failed_records", "partial_records", ...}.

    Checks: unique ad_ids; every clip reference points to a distinct row; rows follow
    meta.clip.row_ad_ids; npy shape matches meta; vectors finite with L2 norm 1 (±1e-4).
    With a dataset: output ad_id order equals the selected rows (same requirements as the run,
    taken from meta.selection unless given) and no excluded row was processed.
    """
    errors: List[str] = []
    checks: Dict[str, bool] = {}

    def check(name: str, ok: bool, msg: str = "") -> None:
        checks[name] = bool(ok)
        if not ok:
            errors.append(f"{name}: {msg}" if msg else name)

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    meta, recs = data.get("meta", {}), data.get("records", [])
    emb = np.load(npy_path)
    ids = [r.get("ad_id") for r in recs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    check("unique_ad_ids", not dup, f"duplicates {dup}")

    clip = meta.get("clip", {})
    row_ids = clip.get("row_ad_ids", [])
    refs = [(r["ad_id"], r["clip_embedding_reference"]["row"]) for r in recs if r.get("clip_embedding_reference")]
    rows = [row for _, row in refs]
    check("one_row_per_reference", len(rows) == len(set(rows)), "a row is referenced by more than one ad")
    check("rows_contiguous", sorted(rows) == list(range(len(rows))),
          f"referenced rows {sorted(rows)[:10]}... are not 0..{len(rows) - 1}")
    check("rows_match_meta_row_ad_ids",
          all(0 <= row < len(row_ids) and row_ids[row] == ad for ad, row in refs) and len(row_ids) == len(refs),
          "clip_embedding_reference rows disagree with meta.clip.row_ad_ids")
    check("npy_rows_match_references", emb.shape[0] == len(refs) == clip.get("n_embedded", emb.shape[0]),
          f"npy has {emb.shape[0]} rows, {len(refs)} references, meta n_embedded={clip.get('n_embedded')}")
    if emb.shape[0]:
        check("npy_dim_matches_meta", emb.ndim == 2 and emb.shape[1] == clip.get("embedding_dim"),
              f"npy shape {emb.shape} vs meta dim {clip.get('embedding_dim')}")
        finite = bool(np.isfinite(emb).all())
        check("vectors_finite", finite, "NaN/inf in embeddings")
        norms = np.linalg.norm(emb, axis=1) if finite else np.array([np.nan])
        check("vectors_l2_normalised", finite and bool(np.all(np.abs(norms - 1) <= 1e-4)),
              f"norm range [{np.nanmin(norms):.6f}, {np.nanmax(norms):.6f}]")

    if dataset_path is not None:
        req = requirements if requirements is not None else meta.get("selection", {}).get("requirements", {})
        selected, sel = select_from_dataset(dataset_path, base_dir, req)
        want = [r.ad_id for r in selected]
        check("order_matches_selected_dataset", ids == want,
              f"output has {len(ids)} ids, selection has {len(want)}; first difference at "
              f"{next((i for i, (a, b) in enumerate(zip(ids, want)) if a != b), min(len(ids), len(want)))}")
        leaked = sorted(set(ids) & set(sel["excluded_ad_ids"]) - set(want))
        check("no_excluded_rows_processed", not leaked, f"excluded ad_ids present: {leaked}")
        ds_hash = meta.get("selection", {}).get("dataset_sha256")
        if ds_hash:
            check("dataset_unchanged_since_run", ds_hash == sel["dataset_sha256"],
                  "dataset file hash differs from the one recorded at extraction time")

    failed = [{"ad_id": r["ad_id"], "error": r.get("extraction_error")} for r in recs
              if r.get("extraction_status") == "failed"]
    partial = [{"ad_id": r["ad_id"], "error": r.get("extraction_error")} for r in recs
               if r.get("extraction_status") == "partial"]
    return {"ok": not errors, "checks": checks, "errors": errors, "n_records": len(recs),
            "n_embedded": int(emb.shape[0]), "failed_records": failed, "partial_records": partial}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--dataset", type=Path, help="CSV/JSON with ad_id, brand, local_image_path")
    src.add_argument("--images-dir", type=Path, help="directory of images (file stem = ad_id)")
    ap.add_argument("--require", action="append", default=[], metavar="COLUMN=VALUE[,VALUE...]",
                    help="keep only rows whose COLUMN is one of the values; repeatable, all must hold")
    ap.add_argument("--status-column", default=None, help="legacy form of --require COLUMN=...")
    ap.add_argument("--allow-status", nargs="+", default=None)
    ap.add_argument("--validate", action="store_true",
                    help="do not extract; validate --out-json/--out-npy (and --dataset ordering if given)")
    ap.add_argument("--out-json", type=Path, default=VISION_CONFIG["visual_features_json"])
    ap.add_argument("--out-npy", type=Path, default=VISION_CONFIG["clip_embeddings_npy"])
    ap.add_argument("--no-clip", action="store_true")
    ap.add_argument("--no-ocr", action="store_true")
    ap.add_argument("--device", default=None, help="cpu | mps | cuda | auto (default from config: cpu)")
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--clip-model", default=None)
    ap.add_argument("--clip-pretrained", default=None)
    ap.add_argument("--limit", type=int, default=None, help="process only the first N selected records")
    a = ap.parse_args(argv)
    if (a.status_column is None) != (a.allow_status is None):
        ap.error("--status-column and --allow-status must be used together")
    try:
        req = parse_requirements(a.require)
    except ValueError as e:
        ap.error(str(e))
    if a.status_column:
        req.setdefault(a.status_column, list(a.allow_status))
    if a.images_dir and req:
        ap.error("--require/--status-column apply to --dataset only")

    if a.validate:
        res = validate_outputs(a.out_json, a.out_npy, a.dataset, req or None)
        print(json.dumps(res, indent=1))
        sys.exit(0 if res["ok"] else 1)

    if not (a.dataset or a.images_dir):
        ap.error("one of --dataset / --images-dir is required (or use --validate)")
    if a.dataset:
        recs, selection = select_from_dataset(a.dataset, BASE_DIR, req)
        print(f"{selection['n_selected']}/{selection['n_rows']} rows selected; excluded: "
              f"{selection['n_excluded_by_condition'] or 'none'}")
    else:
        recs = records_from_directory(a.images_dir)
        check_unique_ad_ids(recs)
        selection = {"images_dir": str(a.images_dir), "n_selected": len(recs)}
    if a.limit:
        recs = recs[:a.limit]
        selection["limit"] = a.limit
    run(recs, a.out_json, a.out_npy, not a.no_clip, not a.no_ocr, a.batch_size, a.device,
        a.clip_model, a.clip_pretrained, selection=selection)


if __name__ == "__main__":
    main()

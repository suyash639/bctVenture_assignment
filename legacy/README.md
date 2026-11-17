# Legacy (superseded) artefacts

Kept for audit only. Nothing here is imported, tested in CI, or presented as a current result.

| Path | What it was | Why superseded |
|---|---|---|
| `code/src/creative_capturer.py`, `code/scripts/capture_creatives.js` | Original creative capture | Opened bare `?id=<ad_id>` URLs, which load a generic results page rather than the ad, then fell back to the whole document. As a result many images belonged to other ads or advertisers. |
| `code/scripts/update_creative_quality_dataset.py` | Built the "50/50 PASS" creative dataset | Hard-coded another tool's temp files; its PASS labels were never checked against the live cards. |
| `code/scripts/run_pipeline.py`, `code/src/preprocessing/` | Legacy dataset consolidation CLI | Only consolidated the legacy dataset. Replaced by `scripts/build_validated_dataset.py` and `src/pipeline/`. |
| `code/src/image_validator.py` | PNG-header check of legacy captures | Replaced by `src/vision/preprocessing.load_image` (full decode). |
| `tests/test_creatives_integrity.py`, `tests/test_dataset_integrity.py` | Tests of the legacy dataset | Asserted file counts, not correctness. Replaced by `tests/test_validated_dataset.py`. |
| `reports/*.md` | Legacy collection, acquisition and findings reports | Contain claims (e.g. "50/50 creatives verified") that live verification disproved. See `reports/creative_quality_audit.md`. |

Legacy data lives in `data/raw/` (as scraped) and `data/legacy/`. A full byte snapshot with
SHA-256 hashes is in `data/archive/evidence_2026-11-13/`.

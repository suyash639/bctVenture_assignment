# Feature Extraction Report

Generated from `data/processed/visual_features.json` (created 2026-11-13T16:28:55+0530) by `scripts/generate_feature_report.py`.

## Run

- Input selection: {"final_status": ["VERIFIED"]} from `data/processed/validated_dataset.csv` (sha256 `398567d57f2e`)
- Records: **50**; status {'success': 50, 'partial': 0, 'failed': 0}
- CLIP: open_clip:ViT-B-32/laion2b_s34b_b79k on `cpu`, dim 512, 50 embedded; OCR: rapidocr_onnxruntime (ok)
- Elapsed: 27.3 s

## Validation (`src.vision.feature_pipeline --validate`)

| Check | Result |
|---|---|
| unique_ad_ids | PASS |
| one_row_per_reference | PASS |
| rows_contiguous | PASS |
| rows_match_meta_row_ad_ids | PASS |
| npy_rows_match_references | PASS |
| npy_dim_matches_meta | PASS |
| vectors_finite | PASS |
| vectors_l2_normalised | PASS |
| order_matches_selected_dataset | PASS |
| no_excluded_rows_processed | PASS |
| dataset_unchanged_since_run | PASS |

Overall: **PASSED**. Embedding L2 norms: min 1.000000, max 1.000000. Failed records: none; partial: none.

## Feature summary by brand

| Brand | n | orientation | text density | sharpness | colourfulness | layout labels |
|---|---|---|---|---|---|---|
| Himalaya Wellness | 10 | {'square': 6, 'portrait': 4} | median 0.120 (min 0.077, max 0.196, n=10) | median 812.245 (min 458.530, max 1746.540, n=10) | median 54.545 (min 28.260, max 102.010, n=10) | {'product_focused': 3, 'lifestyle': 5, 'unknown': 1, 'educational': 1} |
| Kapiva | 10 | {'portrait': 4, 'square': 6} | median 0.132 (min 0.068, max 0.169, n=10) | median 1047.220 (min 186.520, max 2948.030, n=10) | median 27.305 (min 14.850, max 64.670, n=10) | {'lifestyle': 3, 'product_focused': 6, 'educational': 1} |
| Mamaearth | 10 | {'portrait': 1, 'square': 8, 'landscape': 1} | median 0.094 (min 0.015, max 0.230, n=10) | median 444.165 (min 100.510, max 1714.420, n=10) | median 42.720 (min 15.390, max 55.760, n=10) | {'product_focused': 9, 'lifestyle': 1} |
| MuscleBlaze | 10 | {'portrait': 8, 'square': 1, 'landscape': 1} | median 0.145 (min 0.083, max 0.164, n=10) | median 536.160 (min 162.860, max 1802.150, n=10) | median 33.030 (min 22.120, max 55.170, n=10) | {'product_focused': 2, 'offer_heavy': 1, 'lifestyle': 6, 'educational': 1} |
| OZiva | 10 | {'square': 5, 'portrait': 4, 'landscape': 1} | median 0.132 (min 0.044, max 0.217, n=10) | median 669.965 (min 172.630, max 2477.780, n=10) | median 61.880 (min 35.860, max 69.160, n=10) | {'product_focused': 7, 'lifestyle': 2, 'offer_heavy': 1} |

## OCR coverage

- Creatives with ≥ 1 detected text region: 50/50
- Detected regions: 758; readable (conf ≥ 0.5): 758

## Notes

- Layout labels are rule-based heuristics (`src/vision/layout_classifier.py`) and have not been validated against human labels.
- Devanagari text is detected (it counts toward text density) but mostly not transcribed; ₹ is often dropped.
- These are features, not findings. Clustering and observations are produced by `make analyze`.

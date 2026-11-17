# Final QA Report: real outputs

Run 2026-11-13 ~14:10 IST by the final QA agent, against the frozen dataset
(sha256 `815905080d6f184dd2e54438b859436440f8a61b0448f2fad0f142fca4a39275`, 49 VERIFIED / 21 excluded),
the real feature, clustering, analytics and intelligence outputs, and the export in
`dashboard/public/data/`. Code and data were read-only. The production build ran in a scratch copy,
so the running dev server was not affected.

## 1. Test, lint, type and build results

| Check | Command | Result |
|---|---|---|
| Python tests | `.venv/bin/python -m pytest -q` | **114 passed**, 0 failed |
| Lint | `.venv/bin/ruff check src scripts tests config` | All checks passed |
| Dashboard lint | `npm run lint` | No ESLint warnings or errors |
| Dashboard types | `npx tsc --noEmit` | clean |
| Dashboard tests | `npm test` | 20 passed, 4 skipped (the export contract test needs `EXPORT_DIR`) |
| Contract test on the **real** export | `EXPORT_DIR=$PWD/public/data npx vitest run tests/export_contract.test.ts` | **4/4 passed** |
| Production build (scratch copy) | `npm run build` | 7 static routes. `out/` has every route plus `out/data/{manifest,ads,clusters,insights}.json` and 49 creatives |

## 2. Data consistency (real outputs)

| Check | Result |
|---|---|
| Dataset SHA-256 identical in the dataset file, freeze marker, `manifest.json`, `visual_features.json` `meta.selection` and `run_manifest.json` | PASS |
| Manifest is `provisional: false` and `frozen: true` | PASS |
| `ads.json` has exactly the 49 VERIFIED IDs, with no duplicates | PASS |
| Every exported image exists, is byte-identical to `local_image_path`, and its SHA-256 equals `image_sha256` | PASS (49/49) |
| Brand counts agree across manifest, dataset and `ads.json` (Kapiva 10, OZiva 10, Mamaearth 10, Himalaya Wellness 9, MuscleBlaze 10); `n_excluded` = 21 | PASS |
| Every ad has features and a cluster | PASS (49/49) |
| `clusters.json` covers every ad exactly once, agrees with `ads[].cluster`, representatives are members, `brand_mix` is correct | PASS |
| PCA projection covers all 49 ads | PASS |
| Every insight's `supporting_ad_ids` is a subset of the exported ads (94 insights) | PASS |
| No excluded ad is exported as a record | PASS. The 20 excluded IDs present appear **only** as `replaces_ad_id`, the contract's traceability field. The UI renders it as plain text, not a link. |
| CLIP embeddings are L2-normalised (norms 1.000000–1.000000), the row→ad map is correct, shape is (49, 512) | PASS |
| Feature records follow the VERIFIED dataset order | PASS |
| clip and fused variants: the configs selected in `run_manifest` match their files; both `assignments.csv` cover all 49 with brands filled | PASS (both `agglomerative|linkage=average,metric=cosine,n_clusters=8`) |
| Exported `clusters.json` comes from the clip variant and matches `manifest.pipeline.clustering_config` | PASS |

## 3. Dev server routes (`http://localhost:3000`)

| URL | Status | Type | Bytes |
|---|---|---|---|
| `/` | 200 | text/html | 9415 |
| `/brands/` | 200 | text/html | 9891 |
| `/creatives/` | 200 | text/html | 9857 |
| `/clusters/` | 200 | text/html | 9939 |
| `/insights/` | 200 | text/html | 9998 |
| `/creative/?id=1161164159320391` | 200 | text/html | 9625 |
| `/data/manifest.json` · `ads.json` · `clusters.json` · `insights.json` | 200 | application/json | 838 · 130929 · 16425 · 90766 |
| `/data/creatives/kapiva/1161164159320391.jpg` | 200 | image/jpeg | 22184 |

The pages render on the client, so HTML status alone doesn't prove the data rendered. A browser
inspection with screenshots is the lead's step (`scripts/inspect_dashboard.py`).

## 4. UI-derived statistics vs Python (real `ads.json`)

I ran the dashboard's own helpers in `lib/stats.ts` (`countBy`, `quantiles`,
`meanColourDistribution`) on the real export and compared them with numpy:

| Statistic | Values | Match |
|---|---|---|
| Brand counts | Kapiva 10 · OZiva 10 · Mamaearth 10 · Himalaya Wellness 9 · MuscleBlaze 10 | ✔ |
| Format | static 49 | ✔ |
| Status | Active 49 | ✔ |
| Layout | product_focused 27 · lifestyle 16 · educational 3 · offer_heavy 2 · unknown 1 | ✔ |
| CTA (normalised) | Shop Now 42 · Buy Now 3 · Order Now 2 · Unavailable 2 | ✔ |
| Orientation | square 25 · portrait 21 · landscape 3 | ✔ |
| Text-density quartiles per brand (numpy linear) | medians: Kapiva 0.132, OZiva 0.132, Mamaearth 0.094, Himalaya 0.118, MuscleBlaze 0.145 | ✔ (exact) |
| Mean colour distribution (n = 49) | — | ✔ |

## 5. Confirmed bugs

**None.** Every check above passed.

## 6. Observations (not bugs; for the lead's judgement)

1. The Overview shows silhouette 0.17 and Calinski–Harabasz 2.9 as bare tags, with no indication
   that this means weak cluster separation. Consider a one-line interpretation caveat.
2. The selected k = 8 is the **upper bound** of the default grid (`k_range = range(2, 9)`), so the
   choice sits at the edge of the search space. Worth stating in the clustering report.
3. All 49 ads are `static` and `Active`, so the format and status charts each show a single bar.
   That's accurate, not an error, but the demo should say so.
4. The dev-server log was written to `data/outputs_dev_server.log`, in the `data/` root rather than
   `data/outputs/logs/`. Cosmetic clutter only.

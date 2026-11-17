# Execution Progress — Creative Verification, Recovery & Feature Extraction

Started: 2026-11-13. Status values: PENDING / IN_PROGRESS / BLOCKED / COMPLETED / NEEDS_REVIEW.

## Data contract

- **Ground truth** for advertiser, copy, CTA, dates, landing URL, format and creative is the
  live public Ad Library card whose `Library ID` equals the ad ID
  (`scripts/verify_creatives.py`, one JSON object per ad).
- Raw and legacy files are immutable: `data/raw/*`, `data/processed/all_brands_ads.{csv,json}`, `creatives/*`.
- Creatives are always the card's own asset, downloaded as served: no screenshots, no upscaling.
  Verified assets go to `data/creatives/verified/<brand_slug>/<ad_id>.<ext>`.

## Workstream ownership (no two workstreams write the same file)

| # | Workstream | Owner | Writes |
|---|---|---|---|
| 1 | Existing dataset audit | lead | `data/quality/live_cards.json`, `data/quality/advertiser_verification.csv` |
| 2 | Creative recovery | lead | `data/quality/staging/<ad_id>.*`, `data/creatives/verified/**` |
| 3 | Replacement discovery | sub-agent R | `data/quality/replacement_cards.json`, `data/quality/replacement_candidates.json`, `scripts/discover_replacements.py`, `data/quality/staging/<new ids>` |
| 4 | Image quality & duplicates | lead | `data/quality/image_quality_report.csv`, `data/quality/duplicate_groups.json`, `reports/creative_contact_sheets/` |
| 5 | Dataset integrity | lead | `data/processed/validated_dataset.{csv,json}`, `data/quality/dataset_integrity_report.json` |
| 6 | Vision pipeline readiness | sub-agent V | `src/vision/**`, `tests/test_vision_features.py`, README section 9 |
| — | Final feature run & reports | lead | `data/processed/visual_features.json`, `data/processed/clip_embeddings.npy`, `reports/*.md` |

## Task log

| Task | Status | Notes |
|---|---|---|
| Upgrade verifier (summary-details parsing, landing URL, CTA, hashes, workers, login-wall stop) | COMPLETED | Re-parsed 50 stored cards: 0 unparsed advertisers (was 10). |
| Live re-verification of 50 original IDs | COMPLETED | 50/50 cards found; 50/50 assets recovered from the exact card; 38 brand-owned, 12 other advertisers. Evidence: `data/quality/live_cards.json`, log `data/quality/verify_pass2.log`. |
| Visual review of 50 recovered originals | COMPLETED | Recorded in `data/quality/visual_review.json`: 37 brand creatives pass, 1 VIDEO_ONLY (talking-head poster), 12 other-advertiser rejects. |
| Duplicate analysis (originals) | COMPLETED | 3 exact-byte groups (OZiva ×2, Himalaya ×5, MuscleBlaze ×3); 1 representative kept per group. |
| Originals-only build (dry run) | COMPLETED | 29 VERIFIED (Kapiva 10, OZiva 5, Mamaearth 6, Himalaya 5, MuscleBlaze 3); integrity checks pass. 21 replacement slots open. |
| Replacement discovery (5 brands) | BLOCKED | Sub-agent R finished partially: Meta served empty pages (rate limit) from ~13:16. Accepted candidates: OZiva 13, MuscleBlaze 8, Mamaearth 4, Himalaya 0. Lead review: 24 pass, 1 rejected (OZiva 1641142944454615: product not visible). |
| Rate-limit cool-down + polite resume | IN_PROGRESS | `scripts/resume_verification.sh`: 1 control request, then 1 worker + 3 s delay; aborts on any throttle signal. Order: MuscleBlaze full recapture → Himalaya → Mamaearth spares → MuscleBlaze spares. |
| Himalaya consolidation | IN_PROGRESS | `creatives/himalaya_wellness/` = byte-identical copies of the same 10 IDs; canonical brand `Himalaya Wellness`; official-page allowlist in `config/settings.py` (OFFICIAL_ADVERTISERS). |
| Mamaearth crop/cutout inspection | COMPLETED | Legacy captures were page screenshots of wrong or neighbouring cards; recovered assets are complete (CDN `stp=s600x600` = scale-to-fit, no crop). Sheet: `reports/creative_contact_sheets/mamaearth_legacy_vs_recovered.png`. |
| Evidence archive | COMPLETED | `data/archive/evidence_2026-11-13/` (legacy creatives, pass-2 staging, card JSON) with `MANIFEST.sha256` (139 files). |
| Vision pipeline readiness audit | COMPLETED | Sub-agent V: `--require`, `--validate`, duplicate-ID guard, 3 edge-case bugs fixed. Lead re-ran tests: 47/47 pass (.venv); 36 run, 5 skipped (system py3.9). |
| Image quality & duplicate analysis (replacements) | PENDING | Waits on candidate pool. |
| Validated dataset freeze | PENDING | |
| Feature extraction on frozen dataset | PENDING | |
| Reports | PENDING | |

## Corrections to earlier statements

- The earlier interim summary ("27 match / 14 mismatch / 9 unresolved") was miscounted, and 10
  advertisers had failed to parse because of the "See summary details" card variant. Correct
  pass-1 figures: 38 brand-owned IDs, 12 other-advertiser IDs, 0 unresolved.
- The legacy dataset's "50/50 PASS" labels are invalid. Images were captured from generic
  search pages (bare `?id=` URLs do not open the ad), so many images and metadata rows belong
  to other ads or advertisers.

## Analysis workstreams (started 13:24)

| # | Workstream | Owner | Writes | Status |
|---|---|---|---|---|
| A1 | Feature engineering | agent | `src/features/**`, `tests/test_features.py`, `docs/feature_engineering_audit.md` | IN_PROGRESS |
| A2 | Clustering engine | agent | `src/clustering/**`, `tests/test_clustering.py`, `docs/clustering_methodology.md` | IN_PROGRESS |
| A3 | Visual analytics | agent | `src/analytics/**`, `tests/test_analytics.py`, `docs/visual_analytics_specification.md` | IN_PROGRESS |
| A4 | Creative intelligence | agent | `src/intelligence/**`, `tests/test_intelligence.py`, `docs/creative_intelligence_methodology.md` | IN_PROGRESS |
| A5 | Pipeline integration | lead | `src/pipeline/**`, `config/analysis_pipeline.json`, `tests/test_pipeline.py`, `reports/pipeline_integration_report.md` | IN_PROGRESS |

Shared interface: `docs/analysis_data_contract.md`. Dependencies installed by the lead: scikit-learn 1.9.1 (incl. HDBSCAN), matplotlib 3.11.2.

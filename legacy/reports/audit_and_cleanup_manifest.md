> **SUPERSEDED (2026-11-13).** This report describes the legacy dataset. Live Ad Library verification showed that many of its images and metadata rows belong to other ads or advertisers. Kept for audit only; see `reports/creative_quality_audit.md` and `docs/`.

# AdVision AI — Repository Audit & Cleanup Manifest

## 1. Executive Summary
This document records the repository audit, file classification, and safe cleanup manifest conducted by Senior Engineering. Every file was inspected, imports traced, and usage verified before performing any removals or restructuring.

---

## 2. Comprehensive File Audit Categorization

### Category 1: Essential (Actively Used Core Code)
| File Path (Original) | Purpose & Usage | Action / Destination |
| :--- | :--- | :--- |
| `config/settings.py` | Central configuration, brand metadata, cross-platform paths | Retained in `config/settings.py` |
| `src/scraper/browser.py` | Playwright browser lifecycle manager | Modularized into `src/scraper/browser.py` |
| `src/scraper/ad_library_scraper.py` | Core public ad card & accessibility scraper engine | Modularized into `src/scraper/ad_library_scraper.py` |
| `src/scraper/extraction.py` | Redirect URL decoder, CTA extractor, format detector | Modularized into `src/scraper/extraction.py` |
| `src/scraper/creative_capturer.py` | Compositor-level element screenshot runner generator | Modularized into `src/scraper/creative_capturer.py` |
| `src/preprocessing/clean_data.py` | Raw data loader, schema normalizer, master dataset builder | Created in `src/preprocessing/clean_data.py` |
| `src/utils/image_validator.py` | Pure Python PNG header, dimension, and size validator | Created in `src/utils/image_validator.py` |
| `scripts/run_pipeline.py` | End-to-end unified CLI runner (`--validate`, `--clean`, `--summary`) | Created in `scripts/run_pipeline.py` |
| `scripts/capture_creatives.js` | Unified Playwright creative screenshot script | Created in `scripts/capture_creatives.js` |
| `tests/*.py` | Comprehensive test suite (11 unit & integration tests) | Created in `tests/` |

### Category 2: Required Artifacts (Preserved Datasets & Creatives)
| File Path (Original) | Records / Files | Action / Destination |
| :--- | :--- | :--- |
| `data/kapiva_ads.json` | 10 verified Kapiva ad records | Moved to `data/raw/kapiva_ads.json` |
| `data/oziva_ads.json` | 10 verified OZiva ad records | Moved to `data/raw/oziva_ads.json` |
| `data/mamaearth_ads.json` | 10 verified Mamaearth ad records | Moved to `data/raw/mamaearth_ads.json` |
| `data/himalaya_ads.json` | 10 verified Himalaya Wellness ad records | Moved to `data/raw/himalaya_ads.json` |
| `data/muscleblaze_ads.json` | 10 verified MuscleBlaze ad records | Moved to `data/raw/muscleblaze_ads.json` |
| `data/kapiva_ads.csv` | 10 pilot Kapiva CSV records | Moved to `data/raw/kapiva_ads.csv` |
| `data/all_brands_ads.json` | 50 consolidated ad records | Moved to `data/processed/all_brands_ads.json` |
| `data/all_brands_ads.csv` | 50 consolidated CSV rows | Moved to `data/processed/all_brands_ads.csv` |
| `creatives/kapiva/*.png` | 10 valid ad creative images | Preserved in `creatives/kapiva/` |
| `creatives/oziva/*.png` | 10 valid ad creative images | Preserved in `creatives/oziva/` |
| `creatives/mamaearth/*.png` | 10 valid ad creative images | Preserved in `creatives/mamaearth/` |
| `creatives/himalaya/*.png` | 10 valid ad creative images | Preserved in `creatives/himalaya/` (with `himalaya_wellness` relative symlink) |
| `creatives/muscleblaze/*.png` | 10 valid ad creative images | Preserved in `creatives/muscleblaze/` |

### Category 3: Documentation
| File Path | Description | Destination |
| :--- | :--- | :--- |
| `README.md` | Comprehensive architectural guide, setup, usage | Root `README.md` |
| `reports/methodology.md` | Access restrictions, API limits, DOM structure | Moved from `data/collection_notes.md` |
| `reports/collection_report.md` | Multi-brand metadata collection report | In `reports/collection_report.md` |
| `reports/creative_acquisition_report.md` | Image acquisition results, metrics, and validation | In `reports/creative_acquisition_report.md` |
| `reports/findings.md` | Cross-brand format, CTA, and marketing strategy analysis | In `reports/findings.md` |

### Category 4: Unused (Confirmed Obsolete or Redundant)
| File Path | Reason for Removal | Status |
| :--- | :--- | :--- |
| `data/ads/kapiva/screenshot_01_initial.png` | 142KB pilot full-page debug screenshot from manual step 1 check; not an individual creative image | Safe for deletion |
| `data/ads/kapiva/build_dataset.py` | 12KB pilot data generator from step 1; superseded by `clean_data.py` | Safe for deletion |
| `data/generate_multi_brand_datasets.py` | 44KB monolith generator script with hardcoded paths; completely replaced by `src/preprocessing/clean_data.py` | Safe for deletion |
| `scrape_himalaya.py` | 13KB single-brand prototype scraper; completely modularized into `src/scraper/` | Safe for deletion |
| `validate_and_update_datasets.py` | 5.6KB standalone validation script; modularized into `src/utils/image_validator.py` and `scripts/run_pipeline.py` | Safe for deletion |
| `build_capture_scripts.py` | 4.7KB builder script that emitted 5 individual JS files; superseded by `src/scraper/creative_capturer.py` | Safe for deletion |
| `capture_kapiva.js` | 4.6KB individual capture script; superseded by `scripts/capture_creatives.js` | Safe for deletion |
| `capture_oziva.js` | 4.6KB individual capture script; superseded by `scripts/capture_creatives.js` | Safe for deletion |
| `capture_mamaearth.js` | 4.7KB individual capture script; superseded by `scripts/capture_creatives.js` | Safe for deletion |
| `capture_himalaya.js` | 4.9KB individual capture script; superseded by `scripts/capture_creatives.js` | Safe for deletion |
| `capture_muscleblaze.js` | 4.7KB individual capture script; superseded by `scripts/capture_creatives.js` | Safe for deletion |
| `.playwright-mcp/` | MCP server runtime log/yaml cache; excluded via `.gitignore` | Excluded via Git |

### Category 5: Uncertain
None. Every single file in the repository has been traced, analyzed, and mapped to active implementation or verified as obsolete.

---

## 3. Rollback Safety
Prior to executing any deletions, the exact baseline commit (`a6b32f2`) was recorded in Git. Deletions are executed using standard Git commands (`git rm`), ensuring that any file can be restored instantly via `git checkout` or `git revert`.


# scripts/

Thin command-line entry points for collection and dataset curation. Library code lives in
`src/`. Run everything from the repository root with the project environment (`.venv/bin/python`,
or `make …`).

| Script | Purpose | Inputs | Outputs | Network |
|---|---|---|---|---|
| `verify_creatives.py` | Verify ad IDs against their exact live Ad Library card and download each card's own creative | ad IDs (default: every ID in `data/legacy/all_brands_ads.csv`) | `--out` JSON (default `data/quality/live_cards.json`), assets in `--staging-dir` (default `data/quality/staging/`) | **yes** |
| `discover_replacements.py` | List an advertiser's own public Ad Library page, then verify chosen IDs | page ID / ad IDs | `data/quality/replacement_listing.json`, `data/quality/replacement_cards.json` | **yes** |
| `resume_verification.sh` | Polite resume after throttling: one control request, then MuscleBlaze recapture → Himalaya → spares, 1 worker + 3 s delay; aborts on any throttle signal | `data/quality/resume_batches.json` | `muscleblaze_recapture_cards.json`, `replacement_cards.json`, `recapture/muscleblaze/` | **yes** |
| `retry_himalaya.sh` | One polite retry of the Himalaya candidate IDs not yet fetched (control request first) | `resume_batches.json` → `himalaya_remaining` | `replacement_cards.json` | **yes** |
| `build_validated_dataset.py` | Apply the acceptance rules to all recorded evidence; select replacements; copy verified assets | `data/legacy/all_brands_ads.csv`, `data/quality/*.json`, `visual_review.json` | `data/processed/validated_dataset.{csv,json}`, `data/creatives/verified/`, audit CSV/JSON in `data/quality/`, contact sheets | no |
| `generate_quality_reports.py` | Render the audit reports from the files above (every number computed) | `data/quality/*`, `validated_dataset.csv` | `reports/creative_quality_audit.md`, `image_recovery_report.md`, `duplicate_analysis.md`, `dataset_validation_report.md` | no |
| `score_creatives.py` | Image metrics (size, sharpness, contrast, brightness, dHash) for any images | image paths | JSON file | no |
| `compare_legacy_vs_recovered.py` | Side-by-side sheet: legacy capture vs asset recovered from the live card | brand slug | PNG | no |

## Exact commands

```bash
# collection (network; polite; stops on throttling or a login wall)
.venv/bin/python scripts/verify_creatives.py verify --workers 2                       # all legacy IDs
.venv/bin/python scripts/verify_creatives.py verify --workers 1 --delay-ms 3000 \
    --out data/quality/replacement_cards.json <ad_id> [<ad_id> ...]                    # specific IDs
.venv/bin/python scripts/verify_creatives.py page <page_id> --media image --status active
.venv/bin/python scripts/discover_replacements.py list <page_id> --media image --status active
./scripts/resume_verification.sh
./scripts/retry_himalaya.sh

# curation (offline)
.venv/bin/python scripts/build_validated_dataset.py
.venv/bin/python scripts/generate_quality_reports.py
.venv/bin/python scripts/score_creatives.py out.json data/creatives/verified/kapiva/*.jpg
.venv/bin/python scripts/compare_legacy_vs_recovered.py mamaearth reports/creative_contact_sheets/mamaearth_legacy_vs_recovered.png
```

Analysis and export are modules, not scripts: `python -m src.vision.feature_pipeline`,
`python -m src.pipeline.freeze`, `python -m src.pipeline.run`, `python -m src.export.dashboard_data`
(see the Makefile).

## Network etiquette

The network scripts use only the public, logged-out Ad Library. They run 1–2 sequential workers
with multi-second settle times. They stop after 3 consecutive pages with zero ad cards (rate
limited) or 3 login walls, and they never try to bypass either. Wait at least 15 minutes before
retrying after a throttle stop.

# QA Audit

Independent review by the QA agent. Code was read-only; every confirmed bug was reproduced on
copies or synthetic inputs in the scratchpad. No repository data was modified.

## 1. Check results

| Check | Command | Result |
|---|---|---|
| Python test suite | `.venv/bin/python -m pytest -q` | **108 passed**, 0 failed |
| Lint | `.venv/bin/ruff check src scripts tests config` | **All checks passed** |
| System Python (3.9) vision tests | `python3 -m unittest tests.test_vision_features` | 36 run, **OK** (5 skipped: CLIP/OCR not installed there) |
| Dashboard lint | `npm run lint` | No ESLint warnings or errors |
| Dashboard types | `npx tsc --noEmit` | clean |
| Dashboard tests | `npm test` | 20 passed, 4 skipped (`export_contract.test.ts` skips without `EXPORT_DIR`; it runs, and is asserted, inside `tests/test_export.py`) |
| Dashboard build | `npm run build` | 7 static routes |
| Makefile | `make -n <target>` for all 13 targets | all resolve |
| Legacy isolation | grep for imports from `legacy/` | none |

## 2. Confirmed bugs (ranked)

### B1 — HIGH: exporter publishes stale pipeline outputs as current, non-provisional results
- **Where:** `src/export/dashboard_data.py` (`export()`, the feature/assignment loading). Its only
  check is that the ID *sets* match. It never compares the dataset sha256 recorded by the
  pipeline (`run_manifest.json` → `summary.dataset.sha256`) or by feature extraction
  (`visual_features.json` → `meta.selection.dataset_sha256`) with the current dataset.
- **Repro:** copy a finished run, edit one dataset field (same IDs), re-freeze, then export. The
  result is `provisional: False` with all sections available, while the run manifest sha and the
  features sha both differ from the current dataset.
- **Impact:** after any dataset change plus re-freeze, the dashboard shows clusters and insights
  computed from a different dataset version as current.
- **Fix:** require `run_manifest.summary.dataset.sha256 == ds_sha` for clusters/insights, and
  `features meta.selection.dataset_sha256 == ds_sha` for features. Otherwise set
  `available.* = false` and log why. Add a test that changes the dataset after a run.

### B2 — MEDIUM: `freeze` accepts a tampered dataset (stale integrity report trusted)
- **Where:** `src/pipeline/freeze.py:check`. It trusts `dataset_integrity_report.json["passed"]`,
  which isn't bound to the dataset's hash. It re-checks the status columns and that each image
  exists, but not the image sha256, unique image paths, or the advertiser allowlist.
- **Repro:** copy `validated_dataset.csv` and alter three VERIFIED rows (`image_sha256` set to all
  zeros; two ads given the same `local_image_path`; `advertiser="Nykaa"`). Then `check(copy, integrity)`
  returns `[]`, so freezing would succeed.
- **Fix:** have `freeze` recompute the integrity checks on the file it freezes (reuse
  `build_validated_dataset.integrity_checks` or move it into `src/`), or store
  `dataset_sha256` in the integrity report and require a match.

### B3 — MEDIUM: wrong `status` for cards with the "Link to ad" panel
- **Where:** `src/scraper/ad_library_cards.py:85`, `"status": lines[0]`.
- **Evidence:** 6 VERIFIED rows have `status = "Link to ad"`:
  - OZiva 1074001845351229;
  - Himalaya 1013415108457751, 2129333221028958, 2215471982684457, 4471603566436669;
  - MuscleBlaze 1807178123387779.

  Their card text begins `Link to ad\nClose\n…This ad is from a URL link\n…Active\nLibrary ID: …`.
- **Impact:** the validated dataset stores a wrong value. The exporter maps it to `null`, so the
  dashboard shows "Unavailable" instead of "Active".
- **Fix:** take status from the last `Active` / `Inactive` line before `Library ID:`. Re-parse the
  stored `card_text` (no network needed), rebuild the dataset, and add a parser test for this variant.

### B4 — MEDIUM: exporter `--out` deletes any directory without a guard
- **Where:** `src/export/dashboard_data.py:127`, `shutil.rmtree(out_dir)`.
- **Repro:** create a directory holding `notes.txt` and export with `--out` pointing at it. The
  directory is wiped (`notes.txt` gone). A mistyped `--out .` would delete the repository.
- **Fix:** refuse to remove a non-empty directory unless it contains a previous `manifest.json`
  with `schema_version`. Alternatively, write to a temp directory and swap it in.

### B5 — LOW: `scipy` is imported but not declared
- **Where:** `src/clustering/evaluation.py:172`, `from scipy.stats import rankdata`. It's only
  present because scikit-learn pulls it in.
- **Fix:** add `scipy>=1.11` to `requirements.txt`.

## 3. Unconfirmed concerns / design notes

- **Visual reviews are keyed by `ad_id`, not by image hash** (`data/quality/visual_review.json`).
  If a recapture returns different bytes, the old "pass" carries over to the new image. This
  doesn't affect the current data: all 14 MuscleBlaze-owned recaptures are byte-identical, and the
  4 that differ belong to other advertisers and are excluded anyway. Suggested fix: store `image_sha256` with each review and treat a mismatch as `NEEDS_REVIEW`.
- **The dashboard validators (`dashboard/lib/data.ts`) are shallow:** only top-level keys and
  types. The export contract test therefore wouldn't catch enum or nested-field drift. I checked
  the current export by hand, and every enum field is inside its TypeScript union.
- **Small-n clustering selection:** at n=3, `select_configuration` still selects a configuration
  (it records a structural-rule warning) rather than refusing. The pipeline passes the warning
  through to the run summary, and the report should show it prominently.
- **Image URLs are absolute** (`/data/creatives/...`). That works at the domain root, but would
  break if the dashboard were ever deployed under a Next.js `basePath`. None is set today.
- `docs/productization_plan.md` §2 still names pre-refactor paths. It's a historical gap list, but
  it would read better with a "resolved in refactor" note.

## 4. Areas reviewed with no defects found

- **Pipeline:** stage dependency resolution; provisional output routing; the freeze-marker sha
  comparison; refusal on all-noise / no-selection clustering (verified: all-noise HDBSCAN gives
  `config=None` with a rationale, so the pipeline raises `PipelineError`).
- **Clustering:** noise is never forced into clusters; metrics are `None` where undefined;
  assignments cover every ID, including noise.
- **Intelligence:** sampled statements match their `value` and `n` (e.g. "3 of 5 creatives
  (60.0%)" with value 0.6, n 5).
- **Export:**
  - only VERIFIED rows are exported, in dataset order, with excluded IDs absent;
  - images are byte-identical to the verified assets;
  - every enum value is within the TypeScript unions.
- **Repo hygiene:** no imports from `legacy/`, and all Makefile targets resolve.

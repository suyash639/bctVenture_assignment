# Dataset Validation Report

Outputs: `data/processed/validated_dataset.csv` / `.json` (raw and legacy files untouched).

## Acceptance rules

A record is `final_status = VERIFIED` only if all of these hold:

1. `advertiser_verification_status = VERIFIED`: the live card's advertiser belongs to the brand (brand page, sub-brand page, or a partnership ad naming the brand).
2. `image_verification_status = VERIFIED`: the asset was downloaded from that exact card.
3. `metadata_verification_status = VERIFIED`: metadata comes from the same card, and the start date is present.
4. `image_quality_status = PASS`: objective thresholds are met and a recorded visual review passed it.
5. `duplicate_status` ∈ {UNIQUE, GROUP_REPRESENTATIVE}.

## Counts

- Rows in validated dataset: **71** (all 50 legacy records for traceability + 21 selected replacements)
- **VERIFIED: 50** · EXCLUDED: 21

| Brand | VERIFIED | static | video poster | originals retained | replacements |
|---|---|---|---|---|---|
| Kapiva | 10 | 10 | 0 | 10 | 0 |
| OZiva | 10 | 10 | 0 | 5 | 5 |
| Mamaearth | 10 | 10 | 0 | 6 | 4 |
| Himalaya Wellness | 10 | 10 | 0 | 5 | 5 |
| MuscleBlaze | 10 | 10 | 0 | 3 | 7 |

Exclusion reasons (legacy records):

| Reason (first) | Records |
|---|---|
| duplicate creative of 1048789364407302 | 4 |
| advertiser is 'Nykaa', not Mamaearth | 3 |
| advertiser is 'Snapmint', not MuscleBlaze | 2 |
| advertiser is 'Nykaa Man', not MuscleBlaze | 2 |
| duplicate creative of 1308070633511851 | 2 |
| visual review: video poster is a talking-head frame with a subtitle | 1 |
| advertiser is 'IHG Hotels & Resorts', not OZiva | 1 |
| advertiser is 'Ziva - Elite Active Retirement Community', not OZiva | 1 |
| duplicate creative of 1690263575996817 | 1 |
| advertiser is 'HyugaLife', not OZiva | 1 |
| sharpness 99.76 < 100.0 | 1 |
| advertiser is 'blinkit', not Himalaya Wellness | 1 |
| advertiser is 'HealthKart', not MuscleBlaze | 1 |

## Integrity checks (`data/quality/dataset_integrity_report.json`)

| Check | Result | Detail |
|---|---|---|
| unique ad_id across dataset | PASS |  |
| unique image path per verified ad | PASS |  |
| no identical image bytes across verified ads | PASS |  |
| verified image exists and sha256 matches | PASS |  |
| verified ads: advertiser is an allowlisted official page or partnership | PASS |  |
| brand names are canonical | PASS |  |
| verified ads: all five status fields pass | PASS |  |
| verified ads: start_date parses | PASS |  |
| landing URLs are http(s) when present | PASS |  |
| verified count matches selection | PASS |  |

Overall: **PASSED**.

Optional fields missing on VERIFIED records (left empty as unavailable on the card, never inferred): cta: 2, landing_url: 0, body: 0, end_date: 50.

## Advertiser types among VERIFIED records

| Type | Records |
|---|---|
| brand_page | 31 |
| sub_brand_page | 18 |
| partnership | 1 |

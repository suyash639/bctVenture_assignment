# Himalaya Brand Consolidation

Generated 2026-11-13 13:55 IST from `data/processed/validated_dataset.csv` and `data/quality/*`. The dataset is not frozen yet; the live counts are in `reports/dataset_validation_report.md`.

## 1. Two labels, one set of ads

- The legacy repository had `creatives/himalaya/` and `creatives/himalaya_wellness/`. Git records `himalaya_wellness` as a **symlink** (mode `120000`) pointing to `himalaya/`, so both folders held **the same 10 ad IDs, not 20**. The legacy dataset used the brand label `Himalaya Wellness` for all 10 rows.
- Nothing was double-counted: ad IDs are unique across the validated dataset (enforced by `tests/test_validated_dataset.py`).
- The legacy creatives are preserved in `data/legacy/creatives/`, and the symlink is preserved too.

## 2. Canonical brand mapping (`config/settings.py` → `BRAND_ALIASES`)

| Raw label / folder | Canonical brand |
|---|---|
| Himalaya | Himalaya Wellness |
| Himalaya Wellness | Himalaya Wellness |
| himalaya | Himalaya Wellness |
| himalaya_wellness | Himalaya Wellness |

Every Himalaya row in `validated_dataset.csv` has `brand = Himalaya Wellness`, and the original label is kept in `legacy_brand_label`.

## 3. Official advertiser allowlist and evidence

An advertiser counts as Himalaya Wellness only if its exact page name is in `OFFICIAL_ADVERTISERS['Himalaya Wellness']` (with a matching page handle on the card), or it is a partnership ad naming one of those pages. Look-alike names such as "Himalayan Organics" are **not** merged automatically: they get `advertiser_verification_status = NEEDS_REVIEW`.

| Page name (allowlist) | Page handle on card | Numeric page ID | How found |
|---|---|---|---|
| Himalaya Hair Care | HimalayaHairCare | 991334447553447 | page_id/page_name embedded in single-ad page HTML (ad 2280990806062372) |
| Himalaya Personal Care | HimalayaPersonalCare | 292336350791080 | page_id/page_name embedded in single-ad page HTML (ad 1127418319612582) |

The legacy dataset listed page names such as `Himalaya BabyCare` and `Thepink.journey with Himalaya Wellness`. The live cards show different advertisers for those IDs (table below), so the live card was used.

## 4. The 10 legacy Himalaya IDs

| Ad ID | Legacy page name | Live advertiser | Advertiser check | Card: ads using this creative | Duplicate status | Final |
|---|---|---|---|---|---|---|
| 1723845068824942 | Thepink.journey with Himalaya Wellness | Himalaya Hair Care | VERIFIED | 1 | DUPLICATE_OF:1048789364407302 | EXCLUDED |
| 2280990806062372 | Himalaya Wellness with kovid_mittal | Himalaya Hair Care | VERIFIED | 11 | DUPLICATE_OF:1048789364407302 | EXCLUDED |
| 1858609855165049 | jai_lagad_01_ with Himalaya Wellness | Himalaya Hair Care | VERIFIED | 10 | GROUP_REPRESENTATIVE | VERIFIED |
| 4080202645605794 | Himalaya BabyCare | blinkit | MISMATCH | 1 | UNIQUE | EXCLUDED |
| 1048789364407302 | Himalaya Hair Care | Himalaya Hair Care | VERIFIED | 1 | GROUP_REPRESENTATIVE | VERIFIED |
| 1983600392299552 | Himalaya Hair Care | Himalaya Hair Care | VERIFIED | 1 | DUPLICATE_OF:1048789364407302 | EXCLUDED |
| 1620125006185431 | Himalaya Hair Care | Himalaya Hair Care | VERIFIED | 1 | DUPLICATE_OF:1048789364407302 | EXCLUDED |
| 1127418319612582 | Himalaya Personal Care | Himalaya Personal Care | VERIFIED | 1 | UNIQUE | VERIFIED |
| 1598307748623554 | Himalaya Hair Care | Himalaya Hair Care | VERIFIED | 10 | UNIQUE | VERIFIED |
| 1367478492121558 | Himalaya BabyCare | Himalaya Hair Care | VERIFIED | 10 | UNIQUE | VERIFIED |

## 5. Duplicate analysis

- `dup02` (exact, 6 ads): `1048789364407302`, `1115816494122513`, `1620125006185431`, `1723845068824942`, `1983600392299552`, `2280990806062372` → representative `1048789364407302`.
- `dup03` (exact, 2 ads): `1592313662161176`, `1858609855165049` → representative `1858609855165049`.

The Himalaya Hair Care tea-tree shampoo creative runs under many ad IDs; the card itself reports up to 11 ads using one creative. Keeping one representative per identical creative stops a single design being counted several times.

## 6. Replacements

| Legacy ad | Reason | Replacement | Replacement advertiser | Status |
|---|---|---|---|---|
| 1723845068824942 | duplicate creative of 1048789364407302 (dup02) | 4471603566436669 | Himalaya Hair Care | replaced |
| 2280990806062372 | duplicate creative of 1048789364407302 (dup02) | 1013415108457751 | Himalaya Hair Care | replaced |
| 4080202645605794 | advertiser is 'blinkit', not Himalaya Wellness; visual review: not a brand creative: blinkit ad for Plum face wash | 2129333221028958 | Himalaya Hair Care | replaced |
| 1983600392299552 | duplicate creative of 1048789364407302 (dup02) | 2215471982684457 | Himalaya Hair Care | replaced |
| 1620125006185431 | duplicate creative of 1048789364407302 (dup02) | — | — | unavailable_for_visual_analysis |

Replacement candidates came from the Himalaya Hair Care official page listing. Each was verified on its own single-ad card and visually reviewed. Two candidates (`1592313662161176`, `1115816494122513`) were byte-identical to creatives already in the set and were excluded by the duplicate check.

## 7. Result

- **VERIFIED Himalaya Wellness ads: 9** (originals 5, replacements 4). Advertisers: Himalaya Hair Care, Himalaya Personal Care.
- Unresolved: 1 slot (`unavailable_for_visual_analysis`). It isn't padded. A polite retry of the 8 remaining official-page candidates is pending after Meta rate limiting.

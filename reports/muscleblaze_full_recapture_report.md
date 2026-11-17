# MuscleBlaze Full Recapture Report

Generated 2026-11-13 13:55 IST. Evidence: `data/quality/muscleblaze_recapture_cards.json`; assets: `data/quality/recapture/muscleblaze/`; log: `data/quality/resume_run.log`.

## Scope

Every MuscleBlaze ad ID was recaptured from scratch: the 10 legacy IDs and the 8 replacement candidates, 18 in all. Each was captured from its exact public single-ad card (1 worker, 3 s extra delay, after a control request). The earlier MuscleBlaze image files were **not** reused. The validated dataset now takes every MuscleBlaze asset from this recapture (`evidence_source = muscleblaze_recapture_cards.json`).

Completeness: all assets were downloaded as served by the CDN, and every `stp` directive is a scale-to-fit (`dst-jpg_s600x600`) with no crop, so no packaging, text or logo is clipped by the capture. Aspect ratios are the originals'.

## Per-ID results

| Ad ID | Origin | Live advertiser | Advertiser check | Dims | SHA-256 | Identical to earlier capture | CDN stp | Visual / copy check | Final |
|---|---|---|---|---|---|---|---|---|---|
| 1951875575774936 | legacy | Snapmint | MISMATCH | 300x300 | `a61c2ce99a1d` | **no** | dst-jpg_s600x600_tt6 | not a brand creative: Snapmint ad (iPhone) | EXCLUDED |
| 915010216637917 | legacy | MuscleBlaze | VERIFIED | 338x600 | `ba348e1cb54f` | yes | dst-jpg_s600x600_tt6 | 'From reps to recovery' fish oil + MB-Vite combo with offer price | EXCLUDED |
| 1764651081440717 | legacy | Nykaa Man | MISMATCH | 600x600 | `0ae1bb9aa335` | yes | dst-jpg_s600x600_tt6 | not a brand creative: Nykaa Man ad (Paco Rabanne) | EXCLUDED |
| 1886343558542559 | legacy | MuscleBlaze | VERIFIED | 338x600 | `ba348e1cb54f` | yes | dst-jpg_s600x600_tt6 | same creative as 915010216637917 (duplicate check decides) | EXCLUDED |
| 3842344959313280 | legacy | MuscleBlaze | VERIFIED | 600x600 | `f7afd0acafe6` | yes | dst-jpg_s600x600_tt6 | Biozyme 5-in-1 multivitamin with deal price, readable | VERIFIED |
| 1289012628945561 | legacy | HealthKart | MISMATCH | 600x600 | `c75bfa78bf9e` | **no** | dst-jpg_s600x600_tt6 | not a brand creative: HealthKart ad (MuscleBlaze product, reseller advertiser) | EXCLUDED |
| 1116388987911414 | legacy | Snapmint | MISMATCH | 300x300 | `a61c2ce99a1d` | **no** | dst-jpg_s600x600_tt6 | not a brand creative: Snapmint ad (apparel) | EXCLUDED |
| 1308070633511851 | legacy | MuscleBlaze | VERIFIED | 338x600 | `ba348e1cb54f` | yes | dst-jpg_s600x600_tt6 | same creative as 915010216637917 (duplicate check decides) | VERIFIED |
| 881696651677163 | legacy | Nykaa Man | MISMATCH | 600x600 | `75345429c972` | **no** | dst-jpg_s600x600_tt6 | not a brand creative: Nykaa Man ad (Paco Rabanne) | EXCLUDED |
| 1302729857652675 | legacy | MuscleBlaze | VERIFIED | 338x600 | `ccf8671e2cdf` | yes | dst-jpg_s600x600_tt6 | Fish oil 37% off creative, readable | VERIFIED |
| 27068411412827135 | candidate | MuscleBlaze | VERIFIED | 480x600 | `ab51313a5bd5` | yes | dst-jpg_s600x600_tt6 | Biozyme Whey PR 'Why manage two supplements' claim layout; matches card copy (30g protein  | VERIFIED |
| 1021005457107800 | candidate | MuscleBlaze | VERIFIED | 480x600 | `e7da80582dca` | yes | dst-jpg_s600x600_tt6 | Biozyme Whey PR 'Recovery meets Performance' with shaker; matches card copy | VERIFIED |
| 1618366923229535 | candidate | MuscleBlaze | VERIFIED | 338x600 | `410c4e95edf9` | yes | dst-jpg_s600x600_tt6 | Yeast Protein 'Worth the hype' pack shot; matches card copy (yeast protein 26g) | VERIFIED |
| 1807178123387779 | candidate | MuscleBlaze | VERIFIED | 338x600 | `53f6dcfb6739` | yes | dst-jpg_s600x600_tt6 | Iso Clear Whey sachet lifestyle (tennis court); matches card copy (15g isolate) | VERIFIED |
| 4699175186980657 | candidate | MuscleBlaze | VERIFIED | 480x600 | `4e6b08713ab8` | yes | dst-jpg_s600x600_tt6 | 'Your gut feeling' whey lifestyle with product; matches card copy (digestibility) | VERIFIED |
| 1616514576500822 | candidate | MuscleBlaze | VERIFIED | 480x600 | `a89b99336430` | yes | dst-jpg_s600x600_tt6 | 'Light feeling' whey lifestyle with product; matches card copy | VERIFIED |
| 629623256117440 | candidate | MuscleBlaze | VERIFIED | 600x314 | `dec7acd5a656` | yes | dst-jpg_s600x600_tt6 | MB-Vite + Fish Oil combo ₹599 landscape offer; matches card copy; different creative from  | VERIFIED |
| 1072628348484263 | candidate | MuscleBlaze | spare (not selected) | 600x600 | `34e75a2a383d` | yes | dst-jpg_s600x600_tt6 | Creatine Chews launch lifestyle (MB-branded chew in hand); matches card copy | not selected (spare) |

## Findings

- Legacy MuscleBlaze IDs that belong to **other advertisers**: `1951875575774936` (Snapmint), `1764651081440717` (Nykaa Man), `1289012628945561` (HealthKart), `1116388987911414` (Snapmint), `881696651677163` (Nykaa Man). They can't be repaired, only replaced.
- **Reproducibility:** 13/13 MuscleBlaze-owned ads recaptured byte-identical to the earlier capture.
- The 4 assets that differ (`1951875575774936`, `1289012628945561`, `1116388987911414`, `881696651677163`) all belong to other advertisers (Snapmint, HealthKart, Nykaa Man). They look like dynamic or catalogue ads that serve different images per request, and they're excluded anyway.
- Three legacy MuscleBlaze IDs share one creative ("From reps to recovery", identical bytes). One representative is kept.
- Copy-vs-image: each accepted creative was compared with its card copy (product and offer). The reasons are recorded in `data/quality/visual_review.json`.

## Replacement mapping

| Legacy ad | Reason | Replacement | Status |
|---|---|---|---|
| 1951875575774936 | advertiser is 'Snapmint', not MuscleBlaze; longest side 300px < 600; visual review: not a brand creative: Snapmint ad (iPhone) | 27068411412827135 | replaced |
| 915010216637917 | duplicate creative of 1308070633511851 (dup04) | 1021005457107800 | replaced |
| 1764651081440717 | advertiser is 'Nykaa Man', not MuscleBlaze; visual review: not a brand creative: Nykaa Man ad (Paco Rabanne) | 1618366923229535 | replaced |
| 1886343558542559 | duplicate creative of 1308070633511851 (dup04) | 1807178123387779 | replaced |
| 1289012628945561 | advertiser is 'HealthKart', not MuscleBlaze; visual review: not a brand creative: HealthKart ad (MuscleBlaze product, reseller advertiser) | 4699175186980657 | replaced |
| 1116388987911414 | advertiser is 'Snapmint', not MuscleBlaze; longest side 300px < 600; visual review: not a brand creative: Snapmint ad (apparel) | 1616514576500822 | replaced |
| 881696651677163 | advertiser is 'Nykaa Man', not MuscleBlaze; visual review: not a brand creative: Nykaa Man ad (Paco Rabanne) | 629623256117440 | replaced |

## Result

**VERIFIED MuscleBlaze ads: 10** (originals 3, replacements 7). Every one has advertiser `MuscleBlaze`, an asset from the recapture, and a recorded visual review. No record is `UNRECOVERABLE`.

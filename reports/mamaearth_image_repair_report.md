# Mamaearth Image Repair Report

Generated 2026-11-13 13:55 IST. Evidence sheet: `reports/creative_contact_sheets/mamaearth_legacy_vs_recovered.png` (legacy capture on the left, asset recovered from the live card on the right).

## What was wrong with the legacy captures

The legacy Mamaearth images were **browser screenshots of generic Ad Library result pages**, not creatives. They contain Meta UI (header, Filters/Sort buttons), parts of neighbouring cards, and cropped product shots. In most cases the image shows a *different* ad from the ID it's filed under. For example, legacy `1575470834177468` shows a lipstick, but its real creative is a Multani Mitti face wash. Three IDs aren't Mamaearth ads at all: they're Nykaa ads for Palmer's and Kraftpro.

## Repair method

Each ID's exact live card was reopened and the card's own creative was downloaded as served. Nothing was stretched, reconstructed or upscaled. Every CDN directive is `dst-jpg_s600x600`, a scale-to-fit that keeps the whole creative and its aspect ratio. Intentional design crops are preserved and were not treated as capture failures; for example, the scalp close-up in `1756705248927160` is the advertiser's design.

## Per-ID results (legacy IDs)

| Ad ID | Legacy dims | Legacy problem | Live advertiser | Recovered dims | CDN stp | Quality | Sharpness | Final |
|---|---|---|---|---|---|---|---|---|
| 1575470834177468 | 1202x1202 | page screenshot with Meta UI chrome / neighbouring card; image shows a different ad | Mamaearth | 600x600 | dst-jpg_s600x600_tt6 | PASS | 421.04 | VERIFIED |
| 1297573992514723 | 1200x1202 | page screenshot with Meta UI chrome / neighbouring card; image shows a different ad | Mamaearth | 600x600 | dst-jpg_s600x600_tt6 | PASS | 379.27 | VERIFIED |
| 1743457663429642 | 726x1202 | page screenshot of another advertiser's ad (Nykaa) | Nykaa | 600x600 | dst-jpg_s600x600_tt6 | REPLACE | 1435.6 | EXCLUDED |
| 1756705248927160 | 1202x1200 | page screenshot with Meta UI chrome / neighbouring card; image shows a different ad | Mamaearth | 600x600 | dst-jpg_s600x600_tt6 | PASS | 1675.14 | VERIFIED |
| 3326676907721431 | 1200x1200 | page screenshot of another advertiser's ad (Nykaa) | Nykaa | 600x600 | dst-jpg_s600x600_tt6 | REPLACE | 2411.01 | EXCLUDED |
| 984803553943986 | 1202x1202 | page screenshot with Meta UI chrome / neighbouring card; image shows a different ad | Mamaearth | 600x600 | dst-jpg_s600x600_tt6 | REPLACE | 99.76 | EXCLUDED |
| 1166813642586560 | 678x1202 | page screenshot with Meta UI chrome / neighbouring card; image shows a different ad | Mamaearth | 338x600 | dst-jpg_s600x600_tt6 | PASS | 168.47 | VERIFIED |
| 962201073595416 | 1202x1202 | page screenshot with Meta UI chrome / neighbouring card; image shows a different ad | Mamaearth | 600x600 | dst-jpg_s600x600_tt6 | PASS | 467.29 | VERIFIED |
| 1416324700465227 | 1202x1200 | page screenshot with Meta UI chrome / neighbouring card; image shows a different ad | Mamaearth | 600x600 | dst-jpg_s600x600_tt6 | PASS | 564.99 | VERIFIED |
| 2119943695297738 | 726x1202 | page screenshot of another advertiser's ad (Nykaa) | Nykaa | 362x600 | dst-jpg_s600x600_tt6 | REPLACE | 91.2 | EXCLUDED |

- `984803553943986` (a catalogue lipstick on white) scored a sharpness of 99.76 against the pre-set threshold of 100. Its low score comes from flat white area rather than blur, but the threshold was **not tuned after seeing the data**, so the record was replaced. This is documented as a borderline case.

## Replacements

| Legacy ad | Reason | Replacement | Status |
|---|---|---|---|
| 1743457663429642 | advertiser is 'Nykaa', not Mamaearth; visual review: not a brand creative: Nykaa ad for Palmer's | 1101328145809077 | replaced |
| 3326676907721431 | advertiser is 'Nykaa', not Mamaearth; visual review: not a brand creative: Nykaa ad for Palmer's | 1024439270557511 | replaced |
| 984803553943986 | sharpness 99.76 < 100.0 | 1585644086536653 | replaced |
| 2119943695297738 | advertiser is 'Nykaa', not Mamaearth; sharpness 91.2 < 100.0; visual review: not a brand creative: Nykaa ad for Kraftpro hair clips | 1127350820190817 | replaced |

The replacements come from the official Mamaearth page. Each was verified on its own card and visually reviewed. Two further candidates were rejected because they were crops of the existing "Glass Skin Glow" creative (see `data/quality/replacement_candidates.json` → `rejected`).

## Result

**VERIFIED Mamaearth ads: 10** (originals 6, replacements 4). Every asset is complete, uncropped by the capture, and mapped to its correct Ad ID.

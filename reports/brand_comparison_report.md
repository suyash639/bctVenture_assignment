# Brand Comparison Report

Frozen dataset sha256 `398567d57f2e2c47…`, 50 VERIFIED static creatives. Sources: `data/processed/visual_features.json`, `data/processed/validated_dataset.csv`, `data/outputs/intelligence/clip/observations.json`. Brand n is about 10, so a single creative moves any share by about 10 points.

Labels: **OBSERVATION** = measured; **HYPOTHESIS** = an untested interpretation. Nothing here measures ad performance.

## 1. Composition

| Brand | n | format | orientation | advertiser pages |
|---|---|---|---|---|
| Kapiva | 10 | {'static': 10} | {'portrait': 4, 'square': 6} | {'Daily Wellness Solutions by Kapiva': 3, 'Kapiva Performance': 3, 'Kapiva': 2, 'Chronic Health Solutions by Kapiva': 1, 'Kapiva Wellness': 1} |
| OZiva | 10 | {'static': 10} | {'square': 5, 'portrait': 4, 'landscape': 1} | {'OZiva': 9, 'Bharti Singh with OZiva': 1} |
| Mamaearth | 10 | {'static': 10} | {'portrait': 1, 'square': 8, 'landscape': 1} | {'Mamaearth': 10} |
| Himalaya Wellness | 10 | {'static': 10} | {'square': 6, 'portrait': 4} | {'Himalaya Hair Care': 9, 'Himalaya Personal Care': 1} |
| MuscleBlaze | 10 | {'static': 10} | {'portrait': 8, 'square': 1, 'landscape': 1} | {'MuscleBlaze': 10} |

## 2. Text inside the creative (OCR)

| Brand | median text density (min–max) | high-text share (≥0.15) | creatives with ≥1 offer/price cue (layout-rule regex on OCR text) |
|---|---|---|---|
| Kapiva | 0.132 (0.068–0.169) | 4/10 | 5/10 |
| OZiva | 0.132 (0.044–0.217) | 4/10 | 5/10 |
| Mamaearth | 0.094 (0.015–0.230) | 3/10 | 3/10 |
| Himalaya Wellness | 0.120 (0.077–0.196) | 3/10 | 9/10 |
| MuscleBlaze | 0.145 (0.083–0.164) | 4/10 | 8/10 |

The intelligence module (`observations.json`, `offer_text_share`) uses a stricter price/offer-wording pattern and reports Himalaya Wellness 9/10, MuscleBlaze 8/10, OZiva 5/10, Kapiva 2/10, Mamaearth 2/10 (dataset 52.0%). The two counts differ because the layout rules also count per-unit price phrases such as "₹35 per day". Both are OBSERVATIONS of on-image text, not of ad copy.

Text placement (largest share of text area by horizontal third): Kapiva top 9 / middle 1 (n=10); OZiva top 5 / middle 4 / bottom 1 (n=10); Mamaearth middle 6 / top 4 (n=10); Himalaya Wellness middle 5 / top 5 (n=10); MuscleBlaze top 9 / middle 1 (n=10).

Text density is the union area of OCR text boxes ÷ image area. Devanagari counts toward density but is rarely transcribed, so offer cues are under-counted for Hindi- or Marathi-text creatives.

## 3. Colour

| Brand | mean pixel share by colour family (largest first) | white-dominant creatives (≥40% near-white pixels) |
|---|---|---|
| Kapiva | white 57%, black/grey 28%, orange/yellow 9%, green 4% | 8/10 |
| OZiva | white 44%, orange/yellow 21%, green 18%, black/grey 11% | 6/10 |
| Mamaearth | white 59%, orange/yellow 19%, black/grey 14%, red/pink 6% | 6/10 |
| Himalaya Wellness | white 28%, black/grey 23%, green 22%, orange/yellow 15% | 2/10 |
| MuscleBlaze | black/grey 49%, white 28%, blue/cyan 10%, orange/yellow 10% | 4/10 |

## 4. Layout labels (heuristic) and CTAs

| Brand | layout labels | CTA (case-normalised) |
|---|---|---|
| Kapiva | {'product_focused': 6, 'lifestyle': 3, 'educational': 1} | {'Shop Now': 6, 'Buy Now': 3, 'Unavailable': 1} |
| OZiva | {'product_focused': 7, 'lifestyle': 2, 'offer_heavy': 1} | {'Shop Now': 8, 'Order Now': 2} |
| Mamaearth | {'product_focused': 9, 'lifestyle': 1} | {'Shop Now': 10} |
| Himalaya Wellness | {'lifestyle': 5, 'product_focused': 3, 'unknown': 1, 'educational': 1} | {'Shop Now': 9, 'Unavailable': 1} |
| MuscleBlaze | {'lifestyle': 6, 'product_focused': 2, 'offer_heavy': 1, 'educational': 1} | {'Shop Now': 10} |

Layout labels come from transparent rules (OCR cues + CLIP zero-shot scene prompts) and have **not** been validated against human labels. Treat them as descriptive tags.

## 5. Visual similarity (CLIP cosine)

|  | Kapiva | OZiva | Mamaearth | Himalaya Wellness | MuscleBlaze |
|---|---|---|---|---|---|
| Kapiva | 0.395 | 0.370 | 0.342 | 0.388 | 0.343 |
| OZiva | 0.370 | 0.478 | 0.357 | 0.408 | 0.359 |
| Mamaearth | 0.342 | 0.357 | 0.454 | 0.433 | 0.290 |
| Himalaya Wellness | 0.388 | 0.408 | 0.433 | 0.618 | 0.327 |
| MuscleBlaze | 0.343 | 0.359 | 0.290 | 0.327 | 0.483 |

Diagonal = mean pairwise cosine within the brand; off-diagonal = mean cosine between brands.

Most similar cross-brand pairs:

| cosine | ad A | ad B |
|---|---|---|
| 0.645 | `1756705248927160` (Mamaearth) | `2129333221028958` (Himalaya Wellness) |
| 0.618 | `1048789364407302` (Himalaya Wellness) | `1756705248927160` (Mamaearth) |
| 0.584 | `1013415108457751` (Himalaya Wellness) | `1756705248927160` (Mamaearth) |
| 0.574 | `1756705248927160` (Mamaearth) | `1858609855165049` (Himalaya Wellness) |
| 0.570 | `1367478492121558` (Himalaya Wellness) | `1756705248927160` (Mamaearth) |
| 0.566 | `1585644086536653` (Mamaearth) | `4471603566436669` (Himalaya Wellness) |
| 0.552 | `1756705248927160` (Mamaearth) | `2112804086326796` (Himalaya Wellness) |
| 0.543 | `1013415108457751` (Himalaya Wellness) | `1585644086536653` (Mamaearth) |

## 6. Observations

- **OBSERVATION (Kapiva):** within-brand CLIP cosine 0.395 vs 0.361 to other brands; median text density 0.132; largest colour family white (57%); most common layout tag product_focused (6/10).
- **OBSERVATION (OZiva):** within-brand CLIP cosine 0.478 vs 0.373 to other brands; median text density 0.132; largest colour family white (44%); most common layout tag product_focused (7/10).
- **OBSERVATION (Mamaearth):** within-brand CLIP cosine 0.454 vs 0.356 to other brands; median text density 0.094; largest colour family white (59%); most common layout tag product_focused (9/10).
- **OBSERVATION (Himalaya Wellness):** within-brand CLIP cosine 0.618 vs 0.389 to other brands; median text density 0.120; largest colour family white (28%); most common layout tag lifestyle (5/10).
- **OBSERVATION (MuscleBlaze):** within-brand CLIP cosine 0.483 vs 0.330 to other brands; median text density 0.145; largest colour family black/grey (49%); most common layout tag lifestyle (6/10).

**HYPOTHESES (untested):**

- The high within-brand similarity for every brand suggests consistent house styles (packaging colour, templates). An alternative explanation is that a few product lines dominate each brand's sample (e.g. several Himalaya creatives advertise the same tea-tree shampoo).
- The cross-brand nearest pairs share composition (product + person, light backgrounds) rather than brand. Those pairs are the natural candidates for any cross-brand style comparison.

## 7. Caveats

- Mostly *active* ads on one collection date; not a census of each brand's advertising.
- 21 of the 50 creatives are verified replacements chosen from each brand's own page listings. Selection favoured static, distinct creatives, which can shift brand-level shares.

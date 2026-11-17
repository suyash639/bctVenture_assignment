# Creative Intelligence Report

Curated from `data/outputs/intelligence/clip/observations.json` (94 templated observations, all status ok) and `cluster_profiles.json`, which were computed on the frozen dataset (sha256 `398567d57f2e2c47…`, n = 50). Each claim cites the ads behind it. **OBSERVATION** = measured; **HYPOTHESIS** = untested interpretation. Nothing here concerns performance, conversion or effectiveness.

## 1. Visual clusters (clip variant, selected config `agglomerative|linkage=average,metric=cosine,n_clusters=8`)

### Cluster 0 (4 creatives): brands {'Kapiva': 4}

- **OBSERVATION:** layout tags {'product_focused': 4}; orientation {'square': 4}; CTA {'Shop Now': 4}; mean text density 0.148.
- **OBSERVATION (distinguishing features vs dataset mean):** sharpness 2195.722 vs 895.945 (z +1.90); colourfulness 26.800 vs 44.985 (z -1.02); colour_dark_grey 0.423 vs 0.251 (z +0.81).
- Examples (closest to centroid): `950705238104018`, `1595177445638920`, `1515373939961480`. All members: `1515373939961480`, `1521879793036986`, `1595177445638920`, `950705238104018`.

### Cluster 1 (3 creatives): brands {'Kapiva': 1, 'Mamaearth': 1, 'OZiva': 1}

- **OBSERVATION:** layout tags {'lifestyle': 1, 'product_focused': 2}; orientation {'landscape': 1, 'portrait': 2}; CTA {'Shop Now': 3}; mean text density 0.204.
- **OBSERVATION (distinguishing features vs dataset mean):** colour_violet 0.018 vs 0.001 (z +2.24); text_density 0.204 vs 0.126 (z +1.55); colour_red_pink 0.081 vs 0.030 (z +0.99).
- Examples (closest to centroid): `1585644086536653`, `1845266559964841`, `1161164159320391`. All members: `1161164159320391`, `1585644086536653`, `1845266559964841`.

### Cluster 2 (6 creatives): brands {'Kapiva': 5, 'OZiva': 1}

- **OBSERVATION:** layout tags {'educational': 1, 'lifestyle': 3, 'product_focused': 2}; orientation {'portrait': 4, 'square': 2}; CTA {'Buy Now': 3, 'No CTA': 1, 'Shop Now': 2}; mean text density 0.100.
- **OBSERVATION (distinguishing features vs dataset mean):** aspect_ratio 0.748 vs 0.918 (z -0.56); text_density 0.100 vs 0.126 (z -0.51); sharpness 615.215 vs 895.945 (z -0.41).
- Examples (closest to centroid): `1576111410507102`, `2174897743309961`, `1905612623466926`. All members: `1576111410507102`, `1905612623466926`, `2174897743309961`, `2430800034011084`, `3941084412853569`, `4554714978140543`.

### Cluster 3 (12 creatives): brands {'Himalaya Wellness': 10, 'Mamaearth': 2}

- **OBSERVATION:** layout tags {'educational': 1, 'lifestyle': 6, 'product_focused': 4, 'unknown': 1}; orientation {'portrait': 4, 'square': 8}; CTA {'No CTA': 1, 'Shop Now': 11}; mean text density 0.126.
- **OBSERVATION (distinguishing features vs dataset mean):** colourfulness 55.829 vs 44.985 (z +0.61); colour_green 0.183 vs 0.093 (z +0.58); colour_blue_cyan 0.093 vs 0.046 (z +0.51).
- Examples (closest to centroid): `2129333221028958`, `1048789364407302`, `4471603566436669`. All members: `1013415108457751`, `1048789364407302`, `1127418319612582`, `1367478492121558`, `1416324700465227`, `1598307748623554`, `1756705248927160`, `1858609855165049`, `2112804086326796`, `2129333221028958`, `2215471982684457`, `4471603566436669`.

### Cluster 4 (7 creatives): brands {'Mamaearth': 7}

- **OBSERVATION:** layout tags {'product_focused': 7}; orientation {'portrait': 1, 'square': 6}; CTA {'Shop Now': 7}; mean text density 0.093.
- **OBSERVATION (distinguishing features vs dataset mean):** contrast 0.174 vs 0.231 (z -0.89); brightness 0.861 vs 0.695 (z +0.85); colour_dark_grey 0.074 vs 0.251 (z -0.83).
- Examples (closest to centroid): `1575470834177468`, `1127350820190817`, `1166813642586560`. All members: `1024439270557511`, `1101328145809077`, `1127350820190817`, `1166813642586560`, `1297573992514723`, `1575470834177468`, `962201073595416`.

### Cluster 5 (4 creatives): brands {'OZiva': 4}

- **OBSERVATION:** layout tags {'lifestyle': 1, 'offer_heavy': 1, 'product_focused': 2}; orientation {'landscape': 1, 'portrait': 2, 'square': 1}; CTA {'Shop Now': 4}; mean text density 0.168.
- **OBSERVATION (distinguishing features vs dataset mean):** colour_red_pink 0.093 vs 0.030 (z +1.24); colour_green 0.239 vs 0.093 (z +0.95); text_density 0.168 vs 0.126 (z +0.84).
- Examples (closest to centroid): `1781776573039288`, `1814901126595057`, `1650105090459669`. All members: `1650105090459669`, `1669408884833124`, `1781776573039288`, `1814901126595057`.

### Cluster 6 (10 creatives): brands {'MuscleBlaze': 10}

- **OBSERVATION:** layout tags {'educational': 1, 'lifestyle': 6, 'offer_heavy': 1, 'product_focused': 2}; orientation {'landscape': 1, 'portrait': 8, 'square': 1}; CTA {'Shop Now': 10}; mean text density 0.134.
- **OBSERVATION (distinguishing features vs dataset mean):** colour_dark_grey 0.491 vs 0.251 (z +1.13); brightness 0.527 vs 0.695 (z -0.86); colour_blue_cyan 0.098 vs 0.046 (z +0.56).
- Examples (closest to centroid): `1021005457107800`, `4699175186980657`, `1616514576500822`. All members: `1021005457107800`, `1302729857652675`, `1308070633511851`, `1616514576500822`, `1618366923229535`, `1807178123387779`, `27068411412827135`, `3842344959313280`, `4699175186980657`, `629623256117440`.

### Cluster 7 (4 creatives): brands {'OZiva': 4}

- **OBSERVATION:** layout tags {'product_focused': 4}; orientation {'square': 4}; CTA {'Order Now': 2, 'Shop Now': 2}; mean text density 0.079.
- **OBSERVATION (distinguishing features vs dataset mean):** colour_white 0.743 vs 0.431 (z +1.01); text_density 0.079 vs 0.126 (z -0.93); colour_dark_grey 0.056 vs 0.251 (z -0.92).
- Examples (closest to centroid): `1096187009418131`, `1074001845351229`, `1690263575996817`. All members: `1074001845351229`, `1096187009418131`, `1690263575996817`, `3256740111180462`.

## 2. Cross-brand patterns

- **OBSERVATION:** Cross-brand pair #1 by CLIP similarity: 1756705248927160 (Mamaearth) and 2129333221028958 (Himalaya Wellness), cosine 0.645. (supporting: `1756705248927160`, `2129333221028958`)
- **OBSERVATION:** Cross-brand pair #2 by CLIP similarity: 1048789364407302 (Himalaya Wellness) and 1756705248927160 (Mamaearth), cosine 0.618. (supporting: `1048789364407302`, `1756705248927160`)
- **OBSERVATION:** Cross-brand pair #3 by CLIP similarity: 1013415108457751 (Himalaya Wellness) and 1756705248927160 (Mamaearth), cosine 0.584. (supporting: `1013415108457751`, `1756705248927160`)
- **OBSERVATION:** Cross-brand pair #4 by CLIP similarity: 1756705248927160 (Mamaearth) and 1858609855165049 (Himalaya Wellness), cosine 0.574. (supporting: `1756705248927160`, `1858609855165049`)
- **OBSERVATION:** Cross-brand pair #5 by CLIP similarity: 1367478492121558 (Himalaya Wellness) and 1756705248927160 (Mamaearth), cosine 0.570. (supporting: `1367478492121558`, `1756705248927160`)
- **OBSERVATION:** Cluster 1 mixes 3 brands across 3 creatives; the largest brand (Kapiva) accounts for 33.3% (an even split would be 33.3%). (supporting: `1161164159320391`, `1585644086536653`, `1845266559964841`)
- **OBSERVATION:** Cluster 2 mixes 2 brands across 6 creatives; the largest brand (Kapiva) accounts for 83.3% (an even split would be 50.0%). (supporting: `1576111410507102`, `1905612623466926`, `2174897743309961`, `2430800034011084`, `3941084412853569`, `4554714978140543`)
- **OBSERVATION:** Cluster 3 mixes 2 brands across 12 creatives; the largest brand (Himalaya Wellness) accounts for 83.3% (an even split would be 50.0%). (supporting: `1013415108457751`, `1048789364407302`, `1127418319612582`, `1367478492121558`, `1416324700465227`, `1598307748623554`)

## 3. Dataset-wide patterns

- **OBSERVATION:** 49 of 50 labelled creatives (98.0%) received a non-unknown layout label with recorded rule evidence.
- **OBSERVATION:** 0 of 50 creatives with detected text (0.0%) had fewer than 50.0% of text regions transcribed; this is consistent with non-Latin script (e.g. Devanagari) or stylised lettering.
- **OBSERVATION:** 0 of 50 creatives (0.0%) are video posters; the rest are static images.

## 4. Brand-level highlights (selected from the full observation list)

- **OBSERVATION:** 2 of 10 Kapiva creatives (20.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset. (e.g. `1576111410507102`, `1595177445638920`)
- **OBSERVATION:** Mean CLIP cosine similarity between pairs of Kapiva creatives is 0.395 (sd 0.091, 45 pairs), vs 0.361 between Kapiva and other brands' creatives (400 pairs). (e.g. `1161164159320391`, `1515373939961480`, `1521879793036986`)
- **OBSERVATION:** product_focused is the most frequent layout label for Kapiva: 6 of 10 creatives (60.0%), vs 54.0% across the dataset. (e.g. `1515373939961480`, `1521879793036986`, `1595177445638920`)
- **OBSERVATION:** 5 of 10 OZiva creatives (50.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset. (e.g. `1650105090459669`, `1690263575996817`, `1781776573039288`)
- **OBSERVATION:** Mean CLIP cosine similarity between pairs of OZiva creatives is 0.478 (sd 0.102, 45 pairs), vs 0.373 between OZiva and other brands' creatives (400 pairs). (e.g. `1074001845351229`, `1096187009418131`, `1650105090459669`)
- **OBSERVATION:** product_focused is the most frequent layout label for OZiva: 7 of 10 creatives (70.0%), vs 54.0% across the dataset. (e.g. `1074001845351229`, `1096187009418131`, `1669408884833124`)
- **OBSERVATION:** 2 of 10 Mamaearth creatives (20.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset. (e.g. `1024439270557511`, `1585644086536653`)
- **OBSERVATION:** Mean CLIP cosine similarity between pairs of Mamaearth creatives is 0.454 (sd 0.106, 45 pairs), vs 0.356 between Mamaearth and other brands' creatives (400 pairs). (e.g. `1024439270557511`, `1101328145809077`, `1127350820190817`)
- **OBSERVATION:** product_focused is the most frequent layout label for Mamaearth: 9 of 10 creatives (90.0%), vs 54.0% across the dataset. (e.g. `1024439270557511`, `1101328145809077`, `1127350820190817`)
- **OBSERVATION:** 9 of 10 Himalaya Wellness creatives (90.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset. (e.g. `1013415108457751`, `1048789364407302`, `1367478492121558`)
- **OBSERVATION:** Mean CLIP cosine similarity between pairs of Himalaya Wellness creatives is 0.618 (sd 0.086, 45 pairs), vs 0.389 between Himalaya Wellness and other brands' creatives (400 pairs). (e.g. `1013415108457751`, `1048789364407302`, `1127418319612582`)
- **OBSERVATION:** lifestyle is the most frequent layout label for Himalaya Wellness: 5 of 10 creatives (50.0%), vs 34.0% across the dataset. (e.g. `1013415108457751`, `1367478492121558`, `2112804086326796`)
- **OBSERVATION:** 8 of 10 MuscleBlaze creatives (80.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset. (e.g. `1021005457107800`, `1302729857652675`, `1308070633511851`)
- **OBSERVATION:** Mean CLIP cosine similarity between pairs of MuscleBlaze creatives is 0.483 (sd 0.131, 45 pairs), vs 0.330 between MuscleBlaze and other brands' creatives (400 pairs). (e.g. `1021005457107800`, `1302729857652675`, `1308070633511851`)
- **OBSERVATION:** lifestyle is the most frequent layout label for MuscleBlaze: 6 of 10 creatives (60.0%), vs 34.0% across the dataset. (e.g. `1021005457107800`, `1616514576500822`, `1618366923229535`)

## 5. HYPOTHESES (untested; for discussion only)

- Clusters mostly align with brands. CLIP may be encoding brand identity (packaging, palette, recurring talent) more than generic creative format. A within-brand clustering would test whether style groupings exist inside a brand.
- Brands with high on-image offer/price wording may rely on price messaging in-creative rather than in the ad copy. Testing that needs ad-copy analysis and time-series data that this project does not have.
- Cross-brand nearest pairs (product + person compositions) hint at a shared 'lifestyle with product' template across wellness brands. That is a style observation only.

## 6. Limitations

- n = 50 (≈10 per brand); one creative changes a brand share by about 10 points. The clustering structure is weak (silhouette 0.169); see `reports/clustering_evaluation_report.md` for the grid-boundary caveat.
- Layout labels are heuristic. OCR under-reads Devanagari and drops ₹, so offer cues are a lower bound.
- The sample is one snapshot of mostly active ads; replacements were chosen from brand page listings with a preference for static, distinct creatives.

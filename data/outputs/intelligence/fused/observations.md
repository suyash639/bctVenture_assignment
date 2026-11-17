# Creative Intelligence Observations

Records: 50 · brands: Himalaya Wellness, Kapiva, Mamaearth, MuscleBlaze, OZiva · with CLIP embeddings: 50 · clustered: 50 · observations: 90 (0 flagged insufficient data)

Every statement is generated from the numbers shown and lists the ads it rests on. Observations describe creative appearance only.

## Dataset-wide

- **dataset**: 0 of 50 creatives (0.0%) are video posters; the rest are static images.  
  _metric_ `video_poster_share` · n=50 · ads: 1013415108457751, 1021005457107800, 1024439270557511, 1048789364407302, 1074001845351229, 1096187009418131, 1101328145809077, 1127350820190817 … (+42)
- **dataset**: 49 of 50 labelled creatives (98.0%) received a non-unknown layout label with recorded rule evidence.  
  _metric_ `layout_rule_coverage` · n=50 · ads: 1013415108457751, 1021005457107800, 1024439270557511, 1048789364407302, 1074001845351229, 1096187009418131, 1101328145809077, 1127350820190817 … (+41)
- **dataset**: 0 of 50 creatives with detected text (0.0%) had fewer than 50.0% of text regions transcribed; this is consistent with non-Latin script (e.g. Devanagari) or stylised lettering.  
  _metric_ `low_ocr_readability_share` · n=50 · ads: 1013415108457751, 1021005457107800, 1024439270557511, 1048789364407302, 1074001845351229, 1096187009418131, 1101328145809077, 1127350820190817 … (+42)

## By brand

- **brand:Himalaya Wellness**: Mean CLIP cosine similarity between pairs of Himalaya Wellness creatives is 0.618 (sd 0.086, 45 pairs), vs 0.389 between Himalaya Wellness and other brands' creatives (400 pairs).  
  _metric_ `clip_mean_intra_brand_cosine` · n=10 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1598307748623554, 1858609855165049, 2112804086326796, 2129333221028958 … (+2)
- **brand:Himalaya Wellness**: The largest chromatic colour family in Himalaya Wellness creatives is green, covering on average 21.8% of pixels (dataset average 9.3%).  
  _metric_ `mean_colour_family_share` · n=10 · ads: 1048789364407302, 1127418319612582, 1367478492121558, 1598307748623554, 2129333221028958, 4471603566436669
- **brand:Himalaya Wellness**: Shop Now is the most frequent CTA (case-normalised) for Himalaya Wellness: 9 of 10 creatives (90.0%), vs 86.0% across the dataset.  
  _metric_ `cta_share` · n=10 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1598307748623554, 2112804086326796, 2129333221028958, 2215471982684457 … (+1)
- **brand:Himalaya Wellness**: lifestyle is the most frequent layout label for Himalaya Wellness: 5 of 10 creatives (50.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1013415108457751, 1367478492121558, 2112804086326796, 2129333221028958, 4471603566436669
- **brand:Himalaya Wellness**: 9 of 10 Himalaya Wellness creatives (90.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset.  
  _metric_ `offer_text_share` · n=10 · ads: 1013415108457751, 1048789364407302, 1367478492121558, 1598307748623554, 1858609855165049, 2112804086326796, 2129333221028958, 2215471982684457 … (+1)
- **brand:Himalaya Wellness**: square is the most frequent orientation for Himalaya Wellness: 6 of 10 creatives (60.0%), vs 52.0% across the dataset.  
  _metric_ `orientation_share` · n=10 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1858609855165049, 2112804086326796, 4471603566436669
- **brand:Himalaya Wellness**: Mean pairwise colour-distribution distance within Himalaya Wellness is 0.587 (0 = identical palettes, 1 = disjoint), vs 0.554 across all pairs in the dataset.  
  _metric_ `palette_distance_intra_brand` · n=10 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1598307748623554, 1858609855165049, 2112804086326796, 2129333221028958 … (+2)
- **brand:Himalaya Wellness**: 3 of 10 Himalaya Wellness creatives (30.0%) are high-text (density ≥ 0.15); 0 are low-text (< 0.05). Dataset high-text share: 36.0%.  
  _metric_ `high_text_share` · n=10 · ads: 1048789364407302, 1858609855165049, 2215471982684457
- **brand:Himalaya Wellness**: Median OCR text density for Himalaya Wellness is 0.120 (IQR 0.101–0.157, n=10), vs a dataset median of 0.129.  
  _metric_ `text_density_median` · n=10 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1598307748623554, 1858609855165049, 2112804086326796, 2129333221028958 … (+2)
- **brand:Himalaya Wellness**: 2 of 10 Himalaya Wellness creatives (20.0%) are white-dominant (≥ 40.0% near-white pixels), vs 52.0% across the dataset.  
  _metric_ `white_dominant_share` · n=10 · ads: 1127418319612582, 4471603566436669
- **brand:Kapiva**: Mean CLIP cosine similarity between pairs of Kapiva creatives is 0.395 (sd 0.091, 45 pairs), vs 0.361 between Kapiva and other brands' creatives (400 pairs).  
  _metric_ `clip_mean_intra_brand_cosine` · n=10 · ads: 1161164159320391, 1515373939961480, 1521879793036986, 1576111410507102, 1595177445638920, 1905612623466926, 2174897743309961, 2430800034011084 … (+2)
- **brand:Kapiva**: The largest chromatic colour family in Kapiva creatives is orange_yellow, covering on average 8.8% of pixels (dataset average 14.7%).  
  _metric_ `mean_colour_family_share` · n=10 · ads: 1161164159320391, 1515373939961480, 1521879793036986, 1595177445638920, 1905612623466926, 2174897743309961, 2430800034011084, 950705238104018
- **brand:Kapiva**: Shop Now is the most frequent CTA (case-normalised) for Kapiva: 6 of 10 creatives (60.0%), vs 86.0% across the dataset.  
  _metric_ `cta_share` · n=10 · ads: 1161164159320391, 1515373939961480, 1521879793036986, 1595177445638920, 3941084412853569, 950705238104018
- **brand:Kapiva**: product_focused is the most frequent layout label for Kapiva: 6 of 10 creatives (60.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1515373939961480, 1521879793036986, 1595177445638920, 1905612623466926, 3941084412853569, 950705238104018
- **brand:Kapiva**: 2 of 10 Kapiva creatives (20.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset.  
  _metric_ `offer_text_share` · n=10 · ads: 1576111410507102, 1595177445638920
- **brand:Kapiva**: square is the most frequent orientation for Kapiva: 6 of 10 creatives (60.0%), vs 52.0% across the dataset.  
  _metric_ `orientation_share` · n=10 · ads: 1515373939961480, 1521879793036986, 1576111410507102, 1595177445638920, 3941084412853569, 950705238104018
- **brand:Kapiva**: Mean pairwise colour-distribution distance within Kapiva is 0.360 (0 = identical palettes, 1 = disjoint), vs 0.554 across all pairs in the dataset.  
  _metric_ `palette_distance_intra_brand` · n=10 · ads: 1161164159320391, 1515373939961480, 1521879793036986, 1576111410507102, 1595177445638920, 1905612623466926, 2174897743309961, 2430800034011084 … (+2)
- **brand:Kapiva**: 4 of 10 Kapiva creatives (40.0%) are high-text (density ≥ 0.15); 0 are low-text (< 0.05). Dataset high-text share: 36.0%.  
  _metric_ `high_text_share` · n=10 · ads: 1161164159320391, 1515373939961480, 1521879793036986, 2174897743309961
- **brand:Kapiva**: Median OCR text density for Kapiva is 0.132 (IQR 0.086–0.158, n=10), vs a dataset median of 0.129.  
  _metric_ `text_density_median` · n=10 · ads: 1161164159320391, 1515373939961480, 1521879793036986, 1576111410507102, 1595177445638920, 1905612623466926, 2174897743309961, 2430800034011084 … (+2)
- **brand:Kapiva**: 8 of 10 Kapiva creatives (80.0%) are white-dominant (≥ 40.0% near-white pixels), vs 52.0% across the dataset.  
  _metric_ `white_dominant_share` · n=10 · ads: 1161164159320391, 1515373939961480, 1521879793036986, 1595177445638920, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569
- **brand:Mamaearth**: Mean CLIP cosine similarity between pairs of Mamaearth creatives is 0.454 (sd 0.106, 45 pairs), vs 0.356 between Mamaearth and other brands' creatives (400 pairs).  
  _metric_ `clip_mean_intra_brand_cosine` · n=10 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1416324700465227, 1575470834177468, 1585644086536653 … (+2)
- **brand:Mamaearth**: The largest chromatic colour family in Mamaearth creatives is orange_yellow, covering on average 18.8% of pixels (dataset average 14.7%).  
  _metric_ `mean_colour_family_share` · n=10 · ads: 1024439270557511, 1127350820190817, 1166813642586560, 1585644086536653, 1756705248927160
- **brand:Mamaearth**: Shop Now is the most frequent CTA (case-normalised) for Mamaearth: 10 of 10 creatives (100.0%), vs 86.0% across the dataset.  
  _metric_ `cta_share` · n=10 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1416324700465227, 1575470834177468, 1585644086536653 … (+2)
- **brand:Mamaearth**: product_focused is the most frequent layout label for Mamaearth: 9 of 10 creatives (90.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1416324700465227, 1575470834177468, 1585644086536653 … (+1)
- **brand:Mamaearth**: 2 of 10 Mamaearth creatives (20.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset.  
  _metric_ `offer_text_share` · n=10 · ads: 1024439270557511, 1585644086536653
- **brand:Mamaearth**: square is the most frequent orientation for Mamaearth: 8 of 10 creatives (80.0%), vs 52.0% across the dataset.  
  _metric_ `orientation_share` · n=10 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1297573992514723, 1416324700465227, 1575470834177468, 1756705248927160, 962201073595416
- **brand:Mamaearth**: Mean pairwise colour-distribution distance within Mamaearth is 0.477 (0 = identical palettes, 1 = disjoint), vs 0.554 across all pairs in the dataset.  
  _metric_ `palette_distance_intra_brand` · n=10 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1416324700465227, 1575470834177468, 1585644086536653 … (+2)
- **brand:Mamaearth**: 3 of 10 Mamaearth creatives (30.0%) are high-text (density ≥ 0.15); 3 are low-text (< 0.05). Dataset high-text share: 36.0%.  
  _metric_ `high_text_share` · n=10 · ads: 1024439270557511, 1166813642586560, 1585644086536653
- **brand:Mamaearth**: Median OCR text density for Mamaearth is 0.094 (IQR 0.049–0.171, n=10), vs a dataset median of 0.129.  
  _metric_ `text_density_median` · n=10 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1416324700465227, 1575470834177468, 1585644086536653 … (+2)
- **brand:Mamaearth**: 6 of 10 Mamaearth creatives (60.0%) are white-dominant (≥ 40.0% near-white pixels), vs 52.0% across the dataset.  
  _metric_ `white_dominant_share` · n=10 · ads: 1101328145809077, 1127350820190817, 1297573992514723, 1416324700465227, 1575470834177468, 962201073595416
- **brand:MuscleBlaze**: Mean CLIP cosine similarity between pairs of MuscleBlaze creatives is 0.483 (sd 0.131, 45 pairs), vs 0.330 between MuscleBlaze and other brands' creatives (400 pairs).  
  _metric_ `clip_mean_intra_brand_cosine` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **brand:MuscleBlaze**: The largest chromatic colour family in MuscleBlaze creatives is blue_cyan, covering on average 9.8% of pixels (dataset average 4.6%).  
  _metric_ `mean_colour_family_share` · n=10 · ads: 1302729857652675, 1308070633511851, 1618366923229535, 1807178123387779
- **brand:MuscleBlaze**: Shop Now is the most frequent CTA (case-normalised) for MuscleBlaze: 10 of 10 creatives (100.0%), vs 86.0% across the dataset.  
  _metric_ `cta_share` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **brand:MuscleBlaze**: lifestyle is the most frequent layout label for MuscleBlaze: 6 of 10 creatives (60.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1021005457107800, 1616514576500822, 1618366923229535, 1807178123387779, 4699175186980657, 629623256117440
- **brand:MuscleBlaze**: 8 of 10 MuscleBlaze creatives (80.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset.  
  _metric_ `offer_text_share` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 3842344959313280, 4699175186980657, 629623256117440
- **brand:MuscleBlaze**: portrait is the most frequent orientation for MuscleBlaze: 8 of 10 creatives (80.0%), vs 42.0% across the dataset.  
  _metric_ `orientation_share` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 4699175186980657
- **brand:MuscleBlaze**: Mean pairwise colour-distribution distance within MuscleBlaze is 0.547 (0 = identical palettes, 1 = disjoint), vs 0.554 across all pairs in the dataset.  
  _metric_ `palette_distance_intra_brand` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **brand:MuscleBlaze**: 4 of 10 MuscleBlaze creatives (40.0%) are high-text (density ≥ 0.15); 0 are low-text (< 0.05). Dataset high-text share: 36.0%.  
  _metric_ `high_text_share` · n=10 · ads: 1618366923229535, 27068411412827135, 3842344959313280, 4699175186980657
- **brand:MuscleBlaze**: Median OCR text density for MuscleBlaze is 0.145 (IQR 0.111–0.152, n=10), vs a dataset median of 0.129.  
  _metric_ `text_density_median` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **brand:MuscleBlaze**: 4 of 10 MuscleBlaze creatives (40.0%) are white-dominant (≥ 40.0% near-white pixels), vs 52.0% across the dataset.  
  _metric_ `white_dominant_share` · n=10 · ads: 1021005457107800, 27068411412827135, 3842344959313280, 4699175186980657
- **brand:OZiva**: Mean CLIP cosine similarity between pairs of OZiva creatives is 0.478 (sd 0.102, 45 pairs), vs 0.373 between OZiva and other brands' creatives (400 pairs).  
  _metric_ `clip_mean_intra_brand_cosine` · n=10 · ads: 1074001845351229, 1096187009418131, 1650105090459669, 1669408884833124, 1690263575996817, 1781776573039288, 1814901126595057, 1845266559964841 … (+2)
- **brand:OZiva**: The largest chromatic colour family in OZiva creatives is orange_yellow, covering on average 21.0% of pixels (dataset average 14.7%).  
  _metric_ `mean_colour_family_share` · n=10 · ads: 1650105090459669, 1690263575996817, 1781776573039288, 1845266559964841, 3256740111180462
- **brand:OZiva**: Shop Now is the most frequent CTA (case-normalised) for OZiva: 8 of 10 creatives (80.0%), vs 86.0% across the dataset.  
  _metric_ `cta_share` · n=10 · ads: 1074001845351229, 1096187009418131, 1650105090459669, 1669408884833124, 1781776573039288, 1814901126595057, 1845266559964841, 4554714978140543
- **brand:OZiva**: product_focused is the most frequent layout label for OZiva: 7 of 10 creatives (70.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1074001845351229, 1096187009418131, 1669408884833124, 1690263575996817, 1814901126595057, 1845266559964841, 3256740111180462
- **brand:OZiva**: 5 of 10 OZiva creatives (50.0%) show price/offer wording in the image itself (OCR), vs 52.0% across the dataset.  
  _metric_ `offer_text_share` · n=10 · ads: 1650105090459669, 1690263575996817, 1781776573039288, 1845266559964841, 4554714978140543
- **brand:OZiva**: square is the most frequent orientation for OZiva: 5 of 10 creatives (50.0%), vs 52.0% across the dataset.  
  _metric_ `orientation_share` · n=10 · ads: 1074001845351229, 1096187009418131, 1690263575996817, 1814901126595057, 3256740111180462
- **brand:OZiva**: Mean pairwise colour-distribution distance within OZiva is 0.568 (0 = identical palettes, 1 = disjoint), vs 0.554 across all pairs in the dataset.  
  _metric_ `palette_distance_intra_brand` · n=10 · ads: 1074001845351229, 1096187009418131, 1650105090459669, 1669408884833124, 1690263575996817, 1781776573039288, 1814901126595057, 1845266559964841 … (+2)
- **brand:OZiva**: 1 of 10 OZiva creatives (10.0%) were run as partnership ads (creator page "with" the brand).  
  _metric_ `partnership_share` · n=10 · ads: 4554714978140543
- **brand:OZiva**: 4 of 10 OZiva creatives (40.0%) are high-text (density ≥ 0.15); 2 are low-text (< 0.05). Dataset high-text share: 36.0%.  
  _metric_ `high_text_share` · n=10 · ads: 1650105090459669, 1781776573039288, 1814901126595057, 1845266559964841
- **brand:OZiva**: Median OCR text density for OZiva is 0.132 (IQR 0.108–0.169, n=10), vs a dataset median of 0.129.  
  _metric_ `text_density_median` · n=10 · ads: 1074001845351229, 1096187009418131, 1650105090459669, 1669408884833124, 1690263575996817, 1781776573039288, 1814901126595057, 1845266559964841 … (+2)
- **brand:OZiva**: 6 of 10 OZiva creatives (60.0%) are white-dominant (≥ 40.0% near-white pixels), vs 52.0% across the dataset.  
  _metric_ `white_dominant_share` · n=10 · ads: 1074001845351229, 1096187009418131, 1650105090459669, 1690263575996817, 1814901126595057, 3256740111180462

## Cross-brand

- **cross_brand**: Cross-brand pair #1 by CLIP similarity: 1756705248927160 (Mamaearth) and 2129333221028958 (Himalaya Wellness), cosine 0.645.  
  _metric_ `clip_cosine` · n=2 · ads: 1756705248927160, 2129333221028958
- **cross_brand**: Cross-brand pair #2 by CLIP similarity: 1048789364407302 (Himalaya Wellness) and 1756705248927160 (Mamaearth), cosine 0.618.  
  _metric_ `clip_cosine` · n=2 · ads: 1048789364407302, 1756705248927160
- **cross_brand**: Cross-brand pair #3 by CLIP similarity: 1013415108457751 (Himalaya Wellness) and 1756705248927160 (Mamaearth), cosine 0.584.  
  _metric_ `clip_cosine` · n=2 · ads: 1013415108457751, 1756705248927160
- **cross_brand**: Cross-brand pair #4 by CLIP similarity: 1756705248927160 (Mamaearth) and 1858609855165049 (Himalaya Wellness), cosine 0.574.  
  _metric_ `clip_cosine` · n=2 · ads: 1756705248927160, 1858609855165049
- **cross_brand**: Cross-brand pair #5 by CLIP similarity: 1367478492121558 (Himalaya Wellness) and 1756705248927160 (Mamaearth), cosine 0.570.  
  _metric_ `clip_cosine` · n=2 · ads: 1367478492121558, 1756705248927160

## By cluster

- **cluster:0**: Cluster 0 (7 creatives) has mean colour_dark_grey of 0.089 vs 0.251 across the dataset (z = -0.76).  
  _metric_ `cluster_mean_colour_dark_grey` · n=7 · ads: 1074001845351229, 1096187009418131, 1669408884833124, 1690263575996817, 1814901126595057, 3256740111180462, 4554714978140543
- **cluster:0**: Cluster 0 (7 creatives) has mean colour_green of 0.255 vs 0.093 across the dataset (z = +1.05).  
  _metric_ `cluster_mean_colour_green` · n=7 · ads: 1074001845351229, 1096187009418131, 1669408884833124, 1690263575996817, 1814901126595057, 3256740111180462, 4554714978140543
- **cluster:0**: Cluster 0 (7 creatives) has mean colourfulness of 60.904 vs 44.985 across the dataset (z = +0.89).  
  _metric_ `cluster_mean_colourfulness` · n=7 · ads: 1074001845351229, 1096187009418131, 1669408884833124, 1690263575996817, 1814901126595057, 3256740111180462, 4554714978140543
- **cluster:0**: product_focused is the most frequent layout label for cluster 0: 6 of 7 creatives (85.7%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=7 · ads: 1074001845351229, 1096187009418131, 1669408884833124, 1690263575996817, 1814901126595057, 3256740111180462
- **cluster:1**: Cluster 1 (5 creatives) has mean colour_dark_grey of 0.410 vs 0.251 across the dataset (z = +0.75).  
  _metric_ `cluster_mean_colour_dark_grey` · n=5 · ads: 1515373939961480, 1521879793036986, 1576111410507102, 1595177445638920, 950705238104018
- **cluster:1**: Cluster 1 (5 creatives) has mean contrast of 0.281 vs 0.231 across the dataset (z = +0.78).  
  _metric_ `cluster_mean_contrast` · n=5 · ads: 1515373939961480, 1521879793036986, 1576111410507102, 1595177445638920, 950705238104018
- **cluster:1**: Cluster 1 (5 creatives) has mean sharpness of 2102.792 vs 895.945 across the dataset (z = +1.76).  
  _metric_ `cluster_mean_sharpness` · n=5 · ads: 1515373939961480, 1521879793036986, 1576111410507102, 1595177445638920, 950705238104018
- **cluster:1**: product_focused is the most frequent layout label for cluster 1: 4 of 5 creatives (80.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=5 · ads: 1515373939961480, 1521879793036986, 1595177445638920, 950705238104018
- **cluster:2**: Cluster 2 (6 creatives) has mean colour_orange_yellow of 0.477 vs 0.147 across the dataset (z = +1.90).  
  _metric_ `cluster_mean_colour_orange_yellow` · n=6 · ads: 1024439270557511, 1166813642586560, 1585644086536653, 1650105090459669, 1781776573039288, 1845266559964841
- **cluster:2**: Cluster 2 (6 creatives) has mean colour_red_pink of 0.100 vs 0.030 across the dataset (z = +1.37).  
  _metric_ `cluster_mean_colour_red_pink` · n=6 · ads: 1024439270557511, 1166813642586560, 1585644086536653, 1650105090459669, 1781776573039288, 1845266559964841
- **cluster:2**: Cluster 2 (6 creatives) has mean text_density of 0.201 vs 0.126 across the dataset (z = +1.51).  
  _metric_ `cluster_mean_text_density` · n=6 · ads: 1024439270557511, 1166813642586560, 1585644086536653, 1650105090459669, 1781776573039288, 1845266559964841
- **cluster:2**: product_focused is the most frequent layout label for cluster 2: 4 of 6 creatives (66.7%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=6 · ads: 1024439270557511, 1166813642586560, 1585644086536653, 1845266559964841
- **cluster:2**: Cluster 2 mixes 2 brands across 6 creatives; the largest brand (Mamaearth) accounts for 50.0% (an even split would be 50.0%).  
  _metric_ `largest_brand_share_in_cluster` · n=6 · ads: 1024439270557511, 1166813642586560, 1585644086536653, 1650105090459669, 1781776573039288, 1845266559964841
- **cluster:3**: Cluster 3 (5 creatives) has mean aspect_ratio of 0.650 vs 0.918 across the dataset (z = -0.88).  
  _metric_ `cluster_mean_aspect_ratio` · n=5 · ads: 1161164159320391, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569
- **cluster:3**: Cluster 3 (5 creatives) has mean colour_white of 0.670 vs 0.431 across the dataset (z = +0.77).  
  _metric_ `cluster_mean_colour_white` · n=5 · ads: 1161164159320391, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569
- **cluster:3**: Cluster 3 (5 creatives) has mean sharpness of 295.836 vs 895.945 across the dataset (z = -0.88).  
  _metric_ `cluster_mean_sharpness` · n=5 · ads: 1161164159320391, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569
- **cluster:3**: lifestyle is the most frequent layout label for cluster 3: 2 of 5 creatives (40.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=5 · ads: 1161164159320391, 2430800034011084
- **cluster:4**: Cluster 4 (10 creatives) has mean colour_green of 0.208 vs 0.093 across the dataset (z = +0.74).  
  _metric_ `cluster_mean_colour_green` · n=10 · ads: 1013415108457751, 1048789364407302, 1367478492121558, 1598307748623554, 1756705248927160, 1858609855165049, 2112804086326796, 2129333221028958 … (+2)
- **cluster:4**: Cluster 4 (10 creatives) has mean colour_white of 0.235 vs 0.431 across the dataset (z = -0.63).  
  _metric_ `cluster_mean_colour_white` · n=10 · ads: 1013415108457751, 1048789364407302, 1367478492121558, 1598307748623554, 1756705248927160, 1858609855165049, 2112804086326796, 2129333221028958 … (+2)
- **cluster:4**: Cluster 4 (10 creatives) has mean colourfulness of 58.791 vs 44.985 across the dataset (z = +0.77).  
  _metric_ `cluster_mean_colourfulness` · n=10 · ads: 1013415108457751, 1048789364407302, 1367478492121558, 1598307748623554, 1756705248927160, 1858609855165049, 2112804086326796, 2129333221028958 … (+2)
- **cluster:4**: lifestyle is the most frequent layout label for cluster 4: 6 of 10 creatives (60.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1013415108457751, 1367478492121558, 1756705248927160, 2112804086326796, 2129333221028958, 4471603566436669
- **cluster:4**: Cluster 4 mixes 2 brands across 10 creatives; the largest brand (Himalaya Wellness) accounts for 90.0% (an even split would be 50.0%).  
  _metric_ `largest_brand_share_in_cluster` · n=10 · ads: 1013415108457751, 1048789364407302, 1367478492121558, 1598307748623554, 1756705248927160, 1858609855165049, 2112804086326796, 2129333221028958 … (+2)
- **cluster:5**: Cluster 5 (7 creatives) has mean brightness of 0.922 vs 0.695 across the dataset (z = +1.16).  
  _metric_ `cluster_mean_brightness` · n=7 · ads: 1101328145809077, 1127350820190817, 1127418319612582, 1297573992514723, 1416324700465227, 1575470834177468, 962201073595416
- **cluster:5**: Cluster 5 (7 creatives) has mean colour_white of 0.839 vs 0.431 across the dataset (z = +1.31).  
  _metric_ `cluster_mean_colour_white` · n=7 · ads: 1101328145809077, 1127350820190817, 1127418319612582, 1297573992514723, 1416324700465227, 1575470834177468, 962201073595416
- **cluster:5**: Cluster 5 (7 creatives) has mean text_density of 0.059 vs 0.126 across the dataset (z = -1.33).  
  _metric_ `cluster_mean_text_density` · n=7 · ads: 1101328145809077, 1127350820190817, 1127418319612582, 1297573992514723, 1416324700465227, 1575470834177468, 962201073595416
- **cluster:5**: product_focused is the most frequent layout label for cluster 5: 7 of 7 creatives (100.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=7 · ads: 1101328145809077, 1127350820190817, 1127418319612582, 1297573992514723, 1416324700465227, 1575470834177468, 962201073595416
- **cluster:5**: Cluster 5 mixes 2 brands across 7 creatives; the largest brand (Mamaearth) accounts for 85.7% (an even split would be 50.0%).  
  _metric_ `largest_brand_share_in_cluster` · n=7 · ads: 1101328145809077, 1127350820190817, 1127418319612582, 1297573992514723, 1416324700465227, 1575470834177468, 962201073595416
- **cluster:6**: Cluster 6 (10 creatives) has mean brightness of 0.527 vs 0.695 across the dataset (z = -0.86).  
  _metric_ `cluster_mean_brightness` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **cluster:6**: Cluster 6 (10 creatives) has mean colour_blue_cyan of 0.098 vs 0.046 across the dataset (z = +0.56).  
  _metric_ `cluster_mean_colour_blue_cyan` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **cluster:6**: Cluster 6 (10 creatives) has mean colour_dark_grey of 0.491 vs 0.251 across the dataset (z = +1.13).  
  _metric_ `cluster_mean_colour_dark_grey` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **cluster:6**: lifestyle is the most frequent layout label for cluster 6: 6 of 10 creatives (60.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1021005457107800, 1616514576500822, 1618366923229535, 1807178123387779, 4699175186980657, 629623256117440

## Cluster profiles

| Cluster | Size | Brands | Top layout | Mean text density | Representatives |
|---|---|---|---|---|---|
| 0 | 7 | OZiva 7 | product_focused | 0.106 | 1690263575996817, 1096187009418131, 1074001845351229 |
| 1 | 5 | Kapiva 5 | product_focused | 0.132 | 950705238104018, 1595177445638920, 1515373939961480 |
| 2 | 6 | Mamaearth 3, OZiva 3 | product_focused | 0.201 | 1585644086536653, 1650105090459669, 1166813642586560 |
| 3 | 5 | Kapiva 5 | lifestyle | 0.115 | 2174897743309961, 1905612623466926, 2430800034011084 |
| 4 | 10 | Himalaya Wellness 9, Mamaearth 1 | lifestyle | 0.136 | 2129333221028958, 1048789364407302, 4471603566436669 |
| 5 | 7 | Himalaya Wellness 1, Mamaearth 6 | product_focused | 0.059 | 1575470834177468, 1127350820190817, 1297573992514723 |
| 6 | 10 | MuscleBlaze 10 | lifestyle | 0.134 | 1021005457107800, 4699175186980657, 1616514576500822 |

## Standing caveats

- Describes creative appearance only; it says nothing about ad delivery, audience response or outcomes.
- Layout labels come from a rule-based heuristic (src/vision/layout_classifier.py) that has not been validated against human labels.
- OCR reads Latin script and digits; Devanagari text and the ₹ glyph are often not transcribed, so text-based counts are lower bounds.
- CLIP cosine similarity reflects visual-semantic resemblance as learned by the model, not a human judgement of style.
- Colour shares are pixel proportions in 15 HSV buckets; backgrounds and product packaging both contribute.

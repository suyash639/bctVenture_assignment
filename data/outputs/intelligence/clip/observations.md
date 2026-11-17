# Creative Intelligence Observations

Records: 50 · brands: Himalaya Wellness, Kapiva, Mamaearth, MuscleBlaze, OZiva · with CLIP embeddings: 50 · clustered: 50 · observations: 94 (0 flagged insufficient data)

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

- **cluster:0**: Cluster 0 (4 creatives) has mean colour_dark_grey of 0.423 vs 0.251 across the dataset (z = +0.81).  
  _metric_ `cluster_mean_colour_dark_grey` · n=4 · ads: 1515373939961480, 1521879793036986, 1595177445638920, 950705238104018
- **cluster:0**: Cluster 0 (4 creatives) has mean colourfulness of 26.800 vs 44.985 across the dataset (z = -1.02).  
  _metric_ `cluster_mean_colourfulness` · n=4 · ads: 1515373939961480, 1521879793036986, 1595177445638920, 950705238104018
- **cluster:0**: Cluster 0 (4 creatives) has mean sharpness of 2195.722 vs 895.945 across the dataset (z = +1.90).  
  _metric_ `cluster_mean_sharpness` · n=4 · ads: 1515373939961480, 1521879793036986, 1595177445638920, 950705238104018
- **cluster:0**: product_focused is the most frequent layout label for cluster 0: 4 of 4 creatives (100.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=4 · ads: 1515373939961480, 1521879793036986, 1595177445638920, 950705238104018
- **cluster:1**: Cluster 1 (3 creatives) has mean colour_red_pink of 0.081 vs 0.030 across the dataset (z = +0.99).  
  _metric_ `cluster_mean_colour_red_pink` · n=3 · ads: 1161164159320391, 1585644086536653, 1845266559964841
- **cluster:1**: Cluster 1 (3 creatives) has mean colour_violet of 0.018 vs 0.001 across the dataset (z = +2.24).  
  _metric_ `cluster_mean_colour_violet` · n=3 · ads: 1161164159320391, 1585644086536653, 1845266559964841
- **cluster:1**: Cluster 1 (3 creatives) has mean text_density of 0.204 vs 0.126 across the dataset (z = +1.55).  
  _metric_ `cluster_mean_text_density` · n=3 · ads: 1161164159320391, 1585644086536653, 1845266559964841
- **cluster:1**: product_focused is the most frequent layout label for cluster 1: 2 of 3 creatives (66.7%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=3 · ads: 1585644086536653, 1845266559964841
- **cluster:1**: Cluster 1 mixes 3 brands across 3 creatives; the largest brand (Kapiva) accounts for 33.3% (an even split would be 33.3%).  
  _metric_ `largest_brand_share_in_cluster` · n=3 · ads: 1161164159320391, 1585644086536653, 1845266559964841
- **cluster:2**: Cluster 2 (6 creatives) has mean aspect_ratio of 0.748 vs 0.918 across the dataset (z = -0.56).  
  _metric_ `cluster_mean_aspect_ratio` · n=6 · ads: 1576111410507102, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569, 4554714978140543
- **cluster:2**: Cluster 2 (6 creatives) has mean sharpness of 615.215 vs 895.945 across the dataset (z = -0.41).  
  _metric_ `cluster_mean_sharpness` · n=6 · ads: 1576111410507102, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569, 4554714978140543
- **cluster:2**: Cluster 2 (6 creatives) has mean text_density of 0.100 vs 0.126 across the dataset (z = -0.51).  
  _metric_ `cluster_mean_text_density` · n=6 · ads: 1576111410507102, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569, 4554714978140543
- **cluster:2**: lifestyle is the most frequent layout label for cluster 2: 3 of 6 creatives (50.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=6 · ads: 1576111410507102, 2430800034011084, 4554714978140543
- **cluster:2**: Cluster 2 mixes 2 brands across 6 creatives; the largest brand (Kapiva) accounts for 83.3% (an even split would be 50.0%).  
  _metric_ `largest_brand_share_in_cluster` · n=6 · ads: 1576111410507102, 1905612623466926, 2174897743309961, 2430800034011084, 3941084412853569, 4554714978140543
- **cluster:3**: Cluster 3 (12 creatives) has mean colour_blue_cyan of 0.093 vs 0.046 across the dataset (z = +0.51).  
  _metric_ `cluster_mean_colour_blue_cyan` · n=12 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1416324700465227, 1598307748623554, 1756705248927160, 1858609855165049 … (+4)
- **cluster:3**: Cluster 3 (12 creatives) has mean colour_green of 0.183 vs 0.093 across the dataset (z = +0.58).  
  _metric_ `cluster_mean_colour_green` · n=12 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1416324700465227, 1598307748623554, 1756705248927160, 1858609855165049 … (+4)
- **cluster:3**: Cluster 3 (12 creatives) has mean colourfulness of 55.829 vs 44.985 across the dataset (z = +0.61).  
  _metric_ `cluster_mean_colourfulness` · n=12 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1416324700465227, 1598307748623554, 1756705248927160, 1858609855165049 … (+4)
- **cluster:3**: lifestyle is the most frequent layout label for cluster 3: 6 of 12 creatives (50.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=12 · ads: 1013415108457751, 1367478492121558, 1756705248927160, 2112804086326796, 2129333221028958, 4471603566436669
- **cluster:3**: Cluster 3 mixes 2 brands across 12 creatives; the largest brand (Himalaya Wellness) accounts for 83.3% (an even split would be 50.0%).  
  _metric_ `largest_brand_share_in_cluster` · n=12 · ads: 1013415108457751, 1048789364407302, 1127418319612582, 1367478492121558, 1416324700465227, 1598307748623554, 1756705248927160, 1858609855165049 … (+4)
- **cluster:4**: Cluster 4 (7 creatives) has mean brightness of 0.861 vs 0.695 across the dataset (z = +0.85).  
  _metric_ `cluster_mean_brightness` · n=7 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1575470834177468, 962201073595416
- **cluster:4**: Cluster 4 (7 creatives) has mean colour_dark_grey of 0.074 vs 0.251 across the dataset (z = -0.83).  
  _metric_ `cluster_mean_colour_dark_grey` · n=7 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1575470834177468, 962201073595416
- **cluster:4**: Cluster 4 (7 creatives) has mean contrast of 0.174 vs 0.231 across the dataset (z = -0.89).  
  _metric_ `cluster_mean_contrast` · n=7 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1575470834177468, 962201073595416
- **cluster:4**: product_focused is the most frequent layout label for cluster 4: 7 of 7 creatives (100.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=7 · ads: 1024439270557511, 1101328145809077, 1127350820190817, 1166813642586560, 1297573992514723, 1575470834177468, 962201073595416
- **cluster:5**: Cluster 5 (4 creatives) has mean colour_green of 0.239 vs 0.093 across the dataset (z = +0.95).  
  _metric_ `cluster_mean_colour_green` · n=4 · ads: 1650105090459669, 1669408884833124, 1781776573039288, 1814901126595057
- **cluster:5**: Cluster 5 (4 creatives) has mean colour_red_pink of 0.093 vs 0.030 across the dataset (z = +1.24).  
  _metric_ `cluster_mean_colour_red_pink` · n=4 · ads: 1650105090459669, 1669408884833124, 1781776573039288, 1814901126595057
- **cluster:5**: Cluster 5 (4 creatives) has mean text_density of 0.168 vs 0.126 across the dataset (z = +0.84).  
  _metric_ `cluster_mean_text_density` · n=4 · ads: 1650105090459669, 1669408884833124, 1781776573039288, 1814901126595057
- **cluster:5**: product_focused is the most frequent layout label for cluster 5: 2 of 4 creatives (50.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=4 · ads: 1669408884833124, 1814901126595057
- **cluster:6**: Cluster 6 (10 creatives) has mean brightness of 0.527 vs 0.695 across the dataset (z = -0.86).  
  _metric_ `cluster_mean_brightness` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **cluster:6**: Cluster 6 (10 creatives) has mean colour_blue_cyan of 0.098 vs 0.046 across the dataset (z = +0.56).  
  _metric_ `cluster_mean_colour_blue_cyan` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **cluster:6**: Cluster 6 (10 creatives) has mean colour_dark_grey of 0.491 vs 0.251 across the dataset (z = +1.13).  
  _metric_ `cluster_mean_colour_dark_grey` · n=10 · ads: 1021005457107800, 1302729857652675, 1308070633511851, 1616514576500822, 1618366923229535, 1807178123387779, 27068411412827135, 3842344959313280 … (+2)
- **cluster:6**: lifestyle is the most frequent layout label for cluster 6: 6 of 10 creatives (60.0%), vs 34.0% across the dataset.  
  _metric_ `layout_share` · n=10 · ads: 1021005457107800, 1616514576500822, 1618366923229535, 1807178123387779, 4699175186980657, 629623256117440
- **cluster:7**: Cluster 7 (4 creatives) has mean colour_dark_grey of 0.056 vs 0.251 across the dataset (z = -0.92).  
  _metric_ `cluster_mean_colour_dark_grey` · n=4 · ads: 1074001845351229, 1096187009418131, 1690263575996817, 3256740111180462
- **cluster:7**: Cluster 7 (4 creatives) has mean colour_white of 0.743 vs 0.431 across the dataset (z = +1.01).  
  _metric_ `cluster_mean_colour_white` · n=4 · ads: 1074001845351229, 1096187009418131, 1690263575996817, 3256740111180462
- **cluster:7**: Cluster 7 (4 creatives) has mean text_density of 0.079 vs 0.126 across the dataset (z = -0.93).  
  _metric_ `cluster_mean_text_density` · n=4 · ads: 1074001845351229, 1096187009418131, 1690263575996817, 3256740111180462
- **cluster:7**: product_focused is the most frequent layout label for cluster 7: 4 of 4 creatives (100.0%), vs 54.0% across the dataset.  
  _metric_ `layout_share` · n=4 · ads: 1074001845351229, 1096187009418131, 1690263575996817, 3256740111180462

## Cluster profiles

| Cluster | Size | Brands | Top layout | Mean text density | Representatives |
|---|---|---|---|---|---|
| 0 | 4 | Kapiva 4 | product_focused | 0.148 | 950705238104018, 1595177445638920, 1515373939961480 |
| 1 | 3 | Kapiva 1, Mamaearth 1, OZiva 1 | product_focused | 0.204 | 1585644086536653, 1845266559964841, 1161164159320391 |
| 2 | 6 | Kapiva 5, OZiva 1 | lifestyle | 0.100 | 1576111410507102, 2174897743309961, 1905612623466926 |
| 3 | 12 | Himalaya Wellness 10, Mamaearth 2 | lifestyle | 0.126 | 2129333221028958, 1048789364407302, 4471603566436669 |
| 4 | 7 | Mamaearth 7 | product_focused | 0.093 | 1575470834177468, 1127350820190817, 1166813642586560 |
| 5 | 4 | OZiva 4 | product_focused | 0.168 | 1781776573039288, 1814901126595057, 1650105090459669 |
| 6 | 10 | MuscleBlaze 10 | lifestyle | 0.134 | 1021005457107800, 4699175186980657, 1616514576500822 |
| 7 | 4 | OZiva 4 | product_focused | 0.079 | 1096187009418131, 1074001845351229, 1690263575996817 |

## Standing caveats

- Describes creative appearance only; it says nothing about ad delivery, audience response or outcomes.
- Layout labels come from a rule-based heuristic (src/vision/layout_classifier.py) that has not been validated against human labels.
- OCR reads Latin script and digits; Devanagari text and the ₹ glyph are often not transcribed, so text-based counts are lower bounds.
- CLIP cosine similarity reflects visual-semantic resemblance as learned by the model, not a human judgement of style.
- Colour shares are pixel proportions in 15 HSV buckets; backgrounds and product packaging both contribute.

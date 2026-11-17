# Clustering Evaluation Report

Frozen dataset `data/processed/validated_dataset.csv`, sha256 `398567d57f2e2c47e64b28806cabe041e2d9758b6769b194ea98685f6479aa7f`; 50 VERIFIED ads. Pipeline run finished 2026-11-13T16:29:04+0530 (`data/outputs/run_manifest.json`, provisional = False). Every number below is read from `data/outputs/clustering/<variant>/`.

Labels: **OBSERVATION** = measured from the outputs; **HYPOTHESIS** = a possible interpretation that has not been tested.

## 1. Setup

- **clip** (primary): L2-normalised CLIP ViT-B-32 image embeddings (512-d), standardised.
- **fused** (sensitivity check): CLIP plus numeric, colour and layout blocks (weights 1.0 / 0.35 / 0.35 / 0.25; each block ÷ √dims). See `config/analysis_pipeline.json`.
- Grid: K-Means k = 2–8, Agglomerative (Ward; average-linkage cosine) k = 2–8, HDBSCAN min_cluster_size = 3–6, so 25 configs per variant. Selection uses aggregated ranks of silhouette, Davies–Bouldin, Calinski–Harabasz and stability, with structural penalties (`src/clustering/evaluation.py`).

## 2. Variant `clip`: full sweep

| config | k | sizes | noise | silhouette ↑ | DB ↓ | CH ↑ | seed ARI | subsample ARI | neighbour ARI | error |
|---|---|---|---|---|---|---|---|---|---|---|
| kmeans|n_clusters=2,n_init=10 | 2 | [28, 22] | 0% | 0.063 | 3.245 | 4.410 | 0.555 | 0.684 | 0.655 |  |
| kmeans|n_clusters=3,n_init=10 | 3 | [21, 18, 11] | 0% | 0.051 | 3.178 | 3.558 | 0.321 | 0.529 | 0.535 |  |
| kmeans|n_clusters=4,n_init=10 | 4 | [20, 15, 8, 7] | 0% | 0.066 | 2.647 | 3.319 | 0.456 | 0.517 | 0.404 |  |
| kmeans|n_clusters=5,n_init=10 | 5 | [12, 11, 10, 9, 8] | 0% | 0.062 | 2.638 | 3.228 | 0.508 | 0.476 | 0.467 |  |
| kmeans|n_clusters=6,n_init=10 | 6 | [13, 11, 10, 8, 4, 4] | 0% | 0.067 | 2.396 | 2.975 | 0.502 | 0.550 | 0.651 |  |
| kmeans|n_clusters=7,n_init=10 | 7 | [14, 12, 8, 7, 4, 4, 1] | 0% | 0.072 | 2.031 | 2.929 | 0.525 | 0.707 | 0.708 |  |
| kmeans|n_clusters=8,n_init=10 | 8 | [12, 9, 7, 6, 5, 4, 4, 3] | 0% | 0.068 | 2.209 | 2.813 | 0.532 | 0.541 | 0.656 |  |
| agglomerative|linkage=ward,n_clusters=2 | 2 | [40, 10] | 0% | 0.074 | 2.631 | 4.101 | — | 0.758 | 0.487 |  |
| agglomerative|linkage=ward,n_clusters=3 | 3 | [28, 12, 10] | 0% | 0.059 | 2.829 | 3.940 | — | 0.817 | 0.612 |  |
| agglomerative|linkage=ward,n_clusters=4 | 4 | [21, 12, 10, 7] | 0% | 0.072 | 2.703 | 3.716 | — | 0.841 | 0.795 |  |
| agglomerative|linkage=ward,n_clusters=5 | 5 | [17, 12, 10, 7, 4] | 0% | 0.084 | 2.561 | 3.511 | — | 0.841 | 0.833 |  |
| agglomerative|linkage=ward,n_clusters=6 | 6 | [12, 10, 9, 8, 7, 4] | 0% | 0.089 | 2.471 | 3.276 | — | 0.759 | 0.882 |  |
| agglomerative|linkage=ward,n_clusters=7 | 7 | [12, 9, 8, 8, 7, 4, 2] | 0% | 0.095 | 2.294 | 3.130 | — | 0.821 | 0.953 |  |
| agglomerative|linkage=ward,n_clusters=8 | 8 | [12, 8, 8, 7, 7, 4, 2, 2] | 0% | 0.102 | 2.149 | 3.014 | — | 0.785 | 0.954 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=2 | 2 | [28, 22] | 0% | 0.114 | 3.361 | 4.104 | — | 0.671 | 0.679 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=3 | 3 | [22, 14, 14] | 0% | 0.119 | 3.066 | 3.748 | — | 0.742 | 0.722 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=4 | 4 | [14, 14, 12, 10] | 0% | 0.138 | 2.790 | 3.576 | — | 0.718 | 0.858 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=5 | 5 | [14, 14, 12, 7, 3] | 0% | 0.133 | 2.567 | 3.170 | — | 0.765 | 0.915 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=6 | 6 | [14, 12, 8, 7, 6, 3] | 0% | 0.144 | 2.280 | 3.022 | — | 0.838 | 0.881 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=7 | 7 | [12, 10, 8, 7, 6, 4, 3] | 0% | 0.150 | 2.174 | 2.978 | — | 0.848 | 0.915 |  |
| **agglomerative|linkage=average,metric=cosine,n_clusters=8** | 8 | [12, 10, 7, 6, 4, 4, 4, 3] | 0% | 0.169 | 2.031 | 2.945 | — | 0.899 | 0.947 |  |
| hdbscan|min_cluster_size=3 | 4 | [11, 7, 7, 4] | 42% | 0.137 | 1.845 | 4.145 | — | 0.792 | — |  |
| hdbscan|min_cluster_size=4 | 3 | [14, 7, 7] | 44% | 0.145 | 1.997 | 4.474 | — | 0.545 | — |  |
| hdbscan|min_cluster_size=5 | 2 | [22, 5] | 46% | 0.124 | 1.743 | 4.048 | — | 0.505 | — |  |
| hdbscan|min_cluster_size=6 | 0 | [] | 100% | — | — | — | — | 0.700 | — |  |

**Selection rationale (verbatim from `selected_configuration.json`):**

> Selected agglomerative|linkage=average,metric=cosine,n_clusters=8 (score 7.25; lower is better) out of 24 eligible configurations (1 failed or had undefined metrics). Criteria ranks (1 = best of 24): silhouette 1.0, Davies-Bouldin 5.0, Calinski-Harabasz 22.0, stability 1.0. Values: silhouette 0.169, Davies-Bouldin 2.031, Calinski-Harabasz 2.9, subsample ARI 0.8988, 8 clusters, sizes [12, 10, 7, 6, 4, 4, 4, 3], noise 0%. Structural penalties: none. Runners-up: agglomerative|linkage=average,metric=cosine,n_clusters=7 (7.75), agglomerative|linkage=average,metric=cosine,n_clusters=6 (9.00), agglomerative|linkage=ward,n_clusters=5 (10.50).

Warnings: none

## 3. Variant `fused`: full sweep

| config | k | sizes | noise | silhouette ↑ | DB ↓ | CH ↑ | seed ARI | subsample ARI | neighbour ARI | error |
|---|---|---|---|---|---|---|---|---|---|---|
| kmeans|n_clusters=2,n_init=10 | 2 | [40, 10] | 0% | 0.073 | 2.704 | 3.916 | 0.111 | 0.420 | 0.171 |  |
| kmeans|n_clusters=3,n_init=10 | 3 | [21, 15, 14] | 0% | 0.066 | 2.921 | 3.812 | 0.602 | 0.521 | 0.359 |  |
| kmeans|n_clusters=4,n_init=10 | 4 | [18, 16, 10, 6] | 0% | 0.059 | 2.662 | 3.348 | 0.337 | 0.486 | 0.507 |  |
| kmeans|n_clusters=5,n_init=10 | 5 | [15, 11, 11, 7, 6] | 0% | 0.057 | 2.662 | 3.057 | 0.444 | 0.415 | 0.492 |  |
| kmeans|n_clusters=6,n_init=10 | 6 | [15, 14, 7, 6, 4, 4] | 0% | 0.058 | 2.302 | 2.879 | 0.478 | 0.578 | 0.534 |  |
| kmeans|n_clusters=7,n_init=10 | 7 | [13, 11, 9, 6, 6, 4, 1] | 0% | 0.061 | 2.115 | 2.869 | 0.399 | 0.468 | 0.554 |  |
| kmeans|n_clusters=8,n_init=10 | 8 | [14, 11, 7, 5, 4, 3, 3, 3] | 0% | 0.072 | 2.051 | 2.722 | 0.487 | 0.586 | 0.558 |  |
| agglomerative|linkage=ward,n_clusters=2 | 2 | [36, 14] | 0% | 0.064 | 3.094 | 3.904 | — | 0.675 | 0.593 |  |
| agglomerative|linkage=ward,n_clusters=3 | 3 | [26, 14, 10] | 0% | 0.055 | 2.942 | 3.728 | — | 0.531 | 0.701 |  |
| agglomerative|linkage=ward,n_clusters=4 | 4 | [21, 14, 10, 5] | 0% | 0.063 | 2.790 | 3.478 | — | 0.640 | 0.833 |  |
| agglomerative|linkage=ward,n_clusters=5 | 5 | [17, 14, 10, 5, 4] | 0% | 0.067 | 2.599 | 3.299 | — | 0.661 | 0.901 |  |
| agglomerative|linkage=ward,n_clusters=6 | 6 | [17, 12, 10, 5, 4, 2] | 0% | 0.076 | 2.362 | 3.187 | — | 0.694 | 0.875 |  |
| agglomerative|linkage=ward,n_clusters=7 | 7 | [12, 10, 9, 8, 5, 4, 2] | 0% | 0.083 | 2.280 | 3.074 | — | 0.752 | 0.851 |  |
| agglomerative|linkage=ward,n_clusters=8 | 8 | [10, 9, 8, 8, 5, 4, 4, 2] | 0% | 0.088 | 2.211 | 2.995 | — | 0.736 | 0.894 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=2 | 2 | [35, 15] | 0% | 0.100 | 3.216 | 3.779 | — | 0.474 | 0.527 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=3 | 3 | [19, 16, 15] | 0% | 0.119 | 2.994 | 3.721 | — | 0.702 | 0.681 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=4 | 4 | [16, 15, 12, 7] | 0% | 0.128 | 2.650 | 3.375 | — | 0.698 | 0.848 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=5 | 5 | [15, 12, 10, 7, 6] | 0% | 0.139 | 2.461 | 3.244 | — | 0.720 | 0.885 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=6 | 6 | [15, 10, 7, 7, 6, 5] | 0% | 0.147 | 2.312 | 3.082 | — | 0.766 | 0.877 |  |
| **agglomerative|linkage=average,metric=cosine,n_clusters=7** | 7 | [10, 10, 7, 7, 6, 5, 5] | 0% | 0.157 | 2.160 | 3.046 | — | 0.868 | 0.905 |  |
| agglomerative|linkage=average,metric=cosine,n_clusters=8 | 8 | [10, 10, 7, 6, 5, 5, 5, 2] | 0% | 0.159 | 2.048 | 2.926 | — | 0.915 | 0.964 |  |
| hdbscan|min_cluster_size=3 | 4 | [11, 6, 5, 4] | 48% | 0.164 | 1.698 | 4.060 | — | 0.842 | — |  |
| hdbscan|min_cluster_size=4 | 3 | [12, 6, 4] | 56% | 0.145 | 1.759 | 3.710 | — | 0.642 | — |  |
| hdbscan|min_cluster_size=5 | 0 | [] | 100% | — | — | — | — | 0.300 | — |  |
| hdbscan|min_cluster_size=6 | 0 | [] | 100% | — | — | — | — | 1.000 | — |  |

**Selection rationale (verbatim from `selected_configuration.json`):**

> Selected agglomerative|linkage=average,metric=cosine,n_clusters=7 (score 7.25; lower is better) out of 23 eligible configurations (2 failed or had undefined metrics). Criteria ranks (1 = best of 23): silhouette 3.0, Davies-Bouldin 6.0, Calinski-Harabasz 18.0, stability 2.0. Values: silhouette 0.157, Davies-Bouldin 2.160, Calinski-Harabasz 3.0, subsample ARI 0.8678, 7 clusters, sizes [10, 10, 7, 7, 6, 5, 5], noise 0%. Structural penalties: none. The highest-silhouette configuration, hdbscan|min_cluster_size=3 (silhouette 0.164), was not chosen: noise share 48% > 30%. Runners-up: agglomerative|linkage=average,metric=cosine,n_clusters=6 (8.25), agglomerative|linkage=average,metric=cosine,n_clusters=5 (9.50), agglomerative|linkage=average,metric=cosine,n_clusters=4 (10.00).

Warnings: none

## 4. Honest assessment

- **OBSERVATION: the structure is weak.** The selected clip partition has silhouette 0.169. Values below about 0.25 are conventionally read as weak or no substantial structure, so these clusters are groupings of a continuum, not well-separated types.
- **OBSERVATION: the selection sits at the grid boundary.** clip selects k = 8, the largest k searched (grid 2–8); fused selects k = 7. Larger k was **not evaluated**, so the clip choice is the best *within the searched range*, not a demonstrated optimum. With n = 50, larger k would push clusters toward 3–5 members.
- **OBSERVATION: HDBSCAN** produced noise shares of 42% (min_cluster_size=3), 44% (min_cluster_size=4), 46% (min_cluster_size=5), 100% (min_cluster_size=6). Every HDBSCAN run exceeds the 30% noise penalty, so none was selected (see the verbatim rationales above). That is expected for density estimation at n ≈ 50.
- **OBSERVATION: Calinski–Harabasz ranks poorly** for the selected config (CH = 2.94). CH favours few, large clusters; the selection rule deliberately does not rely on any single metric.
- **OBSERVATION: stability is high.** Subsample ARI is 0.899 (80% subsamples, 10 draws) and neighbour-k ARI is 0.947. The partition is reproducible even though its separation is weak.
- **OBSERVATION: the variants partly agree.** ARI between the clip (k = 8) and fused (k = 7) partitions is 0.692. Adding colour, layout and numeric features moves some ads, and the broad grouping holds only as far as that ARI indicates.

## 5. Brand alignment of clusters (clip)

| cluster | size | brand mix | majority brand | purity |
|---|---|---|---|---|
| 0 | 4 | {'Kapiva': 4} | Kapiva | 100% |
| 1 | 3 | {'Kapiva': 1, 'OZiva': 1, 'Mamaearth': 1} | Kapiva | 33% |
| 2 | 6 | {'Kapiva': 5, 'OZiva': 1} | Kapiva | 83% |
| 3 | 12 | {'Mamaearth': 2, 'Himalaya Wellness': 10} | Himalaya Wellness | 83% |
| 4 | 7 | {'Mamaearth': 7} | Mamaearth | 100% |
| 5 | 4 | {'OZiva': 4} | OZiva | 100% |
| 6 | 10 | {'MuscleBlaze': 10} | MuscleBlaze | 100% |
| 7 | 4 | {'OZiva': 4} | OZiva | 100% |

- **OBSERVATION:** the size-weighted brand purity is 90% (clip) and 90% (fused). 5 of 8 clip clusters are single-brand.
- **HYPOTHESIS (untested):** CLIP picks up each brand's consistent visual identity — packaging, palette, recurring templates and models — more strongly than cross-brand creative *styles*. The clusters therefore largely recover brand rather than, say, 'offer creative' versus 'lifestyle creative'. Separating style from brand would need within-brand clustering or brand-residualised embeddings; neither was run.

## 6. Representatives and outliers (clip)

Representatives are the ads closest to the cluster centroid in the clustered feature space; the outlier is the farthest member.

| cluster | size | representatives (closest to centroid) | outlier (farthest member) |
|---|---|---|---|
| 0 | 4 | `950705238104018` (Kapiva, d=0.786), `1595177445638920` (Kapiva, d=0.814), `1515373939961480` (Kapiva, d=0.849), `1521879793036986` (Kapiva, d=0.981) | `1521879793036986` (Kapiva, d=0.981) |
| 1 | 3 | `1585644086536653` (Mamaearth, d=0.709), `1845266559964841` (OZiva, d=0.746), `1161164159320391` (Kapiva, d=0.758) | `1161164159320391` (Kapiva, d=0.758) |
| 2 | 6 | `1576111410507102` (Kapiva, d=0.797), `2174897743309961` (Kapiva, d=0.824), `1905612623466926` (Kapiva, d=0.874), `4554714978140543` (OZiva, d=0.886) | `3941084412853569` (Kapiva, d=0.899) |
| 3 | 12 | `2129333221028958` (Himalaya Wellness, d=0.666), `1048789364407302` (Himalaya Wellness, d=0.691), `4471603566436669` (Himalaya Wellness, d=0.717), `1013415108457751` (Himalaya Wellness, d=0.724) | `1416324700465227` (Mamaearth, d=0.984) |
| 4 | 7 | `1575470834177468` (Mamaearth, d=0.713), `1127350820190817` (Mamaearth, d=0.804), `1166813642586560` (Mamaearth, d=0.823), `1101328145809077` (Mamaearth, d=0.828) | `962201073595416` (Mamaearth, d=1.073) |
| 5 | 4 | `1781776573039288` (OZiva, d=0.673), `1814901126595057` (OZiva, d=0.755), `1650105090459669` (OZiva, d=0.775), `1669408884833124` (OZiva, d=0.792) | `1669408884833124` (OZiva, d=0.792) |
| 6 | 10 | `1021005457107800` (MuscleBlaze, d=0.699), `4699175186980657` (MuscleBlaze, d=0.742), `1616514576500822` (MuscleBlaze, d=0.757), `1302729857652675` (MuscleBlaze, d=0.774) | `3842344959313280` (MuscleBlaze, d=1.059) |
| 7 | 4 | `1096187009418131` (OZiva, d=0.559), `1074001845351229` (OZiva, d=0.567), `1690263575996817` (OZiva, d=0.739), `3256740111180462` (OZiva, d=0.776) | `3256740111180462` (OZiva, d=0.776) |

Contact sheets with every member, labelled with brand and ad_id: `data/outputs/analytics/clip/contact_sheets/cluster_C<k>.png`, with the tile → ad_id mapping in the matching `.csv`. The PCA projection is in `data/outputs/analytics/clip/projections/pca_2d.png`.

## 7. Caveats

- n = 50. Every metric is noisy at this size, and differences between neighbouring configurations (e.g. k = 7 versus 8) are small.
- The clusters describe visual groupings *in this sample* of mostly active ads. They are not market segments and say nothing about ad performance.

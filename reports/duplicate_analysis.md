# Duplicate Analysis

- Exact duplicates: identical SHA-256 of the downloaded bytes.
- Near duplicates: 64-bit difference hash (dHash) with Hamming distance ≤ 6, grouped by union-find.
- Card evidence: Meta's own "N ads use this creative and text" counter (`n_ads_same_creative`).
- Policy: one representative per group enters the final dataset. Others are kept in the dataset as `DUPLICATE_OF:<id>` with `final_status = EXCLUDED`. Identical creatives run under different ad IDs would otherwise over-weight one creative in clustering.

Groups found: **7**.

### dup01 — exact (OZiva)

| Ad ID | Origin | Duplicate status | Sharpness | Card: ads using creative |
|---|---|---|---|---|
| 1690263575996817 | original | GROUP_REPRESENTATIVE | 803.31 | 1 |
| 1778699290118107 | original | DUPLICATE_OF:1690263575996817 | 803.31 | 1 |

Representative kept: `1690263575996817`. Decision: auto: best original by quality.

### dup02 — exact (Himalaya Wellness)

| Ad ID | Origin | Duplicate status | Sharpness | Card: ads using creative |
|---|---|---|---|---|
| 1048789364407302 | original | GROUP_REPRESENTATIVE | 1464.59 | 1 |
| 1115816494122513 | replacement | DUPLICATE_OF:1048789364407302 | 1464.59 | 1 |
| 1620125006185431 | original | DUPLICATE_OF:1048789364407302 | 1464.59 | 1 |
| 1723845068824942 | original | DUPLICATE_OF:1048789364407302 | 1464.59 | 1 |
| 1983600392299552 | original | DUPLICATE_OF:1048789364407302 | 1464.59 | 1 |
| 2280990806062372 | original | DUPLICATE_OF:1048789364407302 | 1464.59 | 11 |

Representative kept: `1048789364407302`. Decision: auto: best original by quality.

### dup03 — exact (Himalaya Wellness)

| Ad ID | Origin | Duplicate status | Sharpness | Card: ads using creative |
|---|---|---|---|---|
| 1592313662161176 | replacement | DUPLICATE_OF:1858609855165049 | 1746.54 | 1 |
| 1858609855165049 | original | GROUP_REPRESENTATIVE | 1746.54 | 10 |

Representative kept: `1858609855165049`. Decision: auto: best original by quality.

### dup04 — exact (MuscleBlaze)

| Ad ID | Origin | Duplicate status | Sharpness | Card: ads using creative |
|---|---|---|---|---|
| 1308070633511851 | original | GROUP_REPRESENTATIVE | 249.44 | 1 |
| 1886343558542559 | original | DUPLICATE_OF:1308070633511851 | 249.44 | 1 |
| 915010216637917 | original | DUPLICATE_OF:1308070633511851 | 249.44 | 1 |

Representative kept: `1308070633511851`. Decision: auto: best original by quality.

### dup05 — exact (Himalaya Wellness)

| Ad ID | Origin | Duplicate status | Sharpness | Card: ads using creative |
|---|---|---|---|---|
| 4471603566436669 | replacement | GROUP_REPRESENTATIVE | 1221.33 | 1 |
| 4501524406843689 | replacement | DUPLICATE_OF:4471603566436669 | 1221.33 | 1 |

Representative kept: `4471603566436669`. Decision: auto: best original by quality.

### dup06 — exact (Himalaya Wellness)

| Ad ID | Origin | Duplicate status | Sharpness | Card: ads using creative |
|---|---|---|---|---|
| 1126182349975686 | replacement | GROUP_REPRESENTATIVE | 1356.27 | 1 |
| 27894864253480176 | replacement | DUPLICATE_OF:1126182349975686 | 1356.27 | 1 |

Representative kept: `1126182349975686`. Decision: auto: best original by quality.

### dup07 — exact (Himalaya Wellness)

| Ad ID | Origin | Duplicate status | Sharpness | Card: ads using creative |
|---|---|---|---|---|
| 2521696481648312 | replacement | GROUP_REPRESENTATIVE | 997.1 | 1 |
| 4028706644097800 | replacement | DUPLICATE_OF:2521696481648312 | 997.1 | 1 |

Representative kept: `2521696481648312`. Decision: auto: best original by quality.

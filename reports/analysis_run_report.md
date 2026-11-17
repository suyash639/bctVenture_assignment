# Analysis Run Report

- Finished: 2026-11-13T16:29:04+0530 · config `config/analysis_pipeline.json` (sha256 `206522d9cb9e`)
- Dataset: `data/processed/validated_dataset.csv` sha256 `398567d57f2e`, 50 selected of 71 rows ({'final_status': 'VERIFIED'})
- Per brand: {'Himalaya Wellness': 10, 'Kapiva': 10, 'Mamaearth': 10, 'MuscleBlaze': 10, 'OZiva': 10}

## Stages

| Stage | Seconds |
|---|---|
| validate | 0.05 |
| extract | 0.0 |
| features | 0.01 |
| clustering | 5.21 |
| analytics | 2.47 |
| intelligence | 0.03 |

## Summary

```json
{
 "frozen": true,
 "features_validation": {
  "passed": true,
  "n_records": 50
 },
 "features": {
  "clip": {
   "n_rows": 50,
   "n_dims": 512,
   "excluded": []
  },
  "fused": {
   "n_rows": 50,
   "n_dims": 551,
   "excluded": []
  }
 },
 "feature_issues": 0,
 "clustering": {
  "clip": {
   "selected": "agglomerative|linkage=average,metric=cosine,n_clusters=8",
   "warnings": [],
   "n_configs": 25,
   "outputs": {
    "sweep": "data/outputs/clustering/clip/sweep_results.json",
    "selection": "data/outputs/clustering/clip/selected_configuration.json",
    "assignments": "data/outputs/clustering/clip/assignments.csv"
   }
  },
  "fused": {
   "selected": "agglomerative|linkage=average,metric=cosine,n_clusters=7",
   "warnings": [],
   "n_configs": 25,
   "outputs": {
    "sweep": "data/outputs/clustering/fused/sweep_results.json",
    "selection": "data/outputs/clustering/fused/selected_configuration.json",
    "assignments": "data/outputs/clustering/fused/assignments.csv"
   }
  }
 },
 "analytics": {
  "clip": {
   "n_artifacts": 0,
   "skipped": []
  },
  "fused": {
   "n_artifacts": 0,
   "skipped": []
  }
 },
 "intelligence": {
  "clip": {
   "n_observations": 94,
   "by_status": {
    "ok": 94
   }
  },
  "fused": {
   "n_observations": 90,
   "by_status": {
    "ok": 90
   }
  }
 }
}
```

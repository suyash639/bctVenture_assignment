"""Clustering engine: K-Means, Agglomerative and HDBSCAN with metrics, stability and selection.

See docs/clustering_methodology.md and docs/analysis_data_contract.md.
"""

from src.clustering.core import ClusterConfig, ClusteringResult, compute_metrics, run_clustering
from src.clustering.evaluation import (
                                       Selection,
                                       SweepResult,
                                       default_grid,
                                       run_sweep,
                                       seed_stability,
                                       select_configuration,
                                       subsample_stability,
)
from src.clustering.io import read_assignments, write_all, write_assignments, write_selection, write_sweep

__all__ = ["ClusterConfig", "ClusteringResult", "compute_metrics", "run_clustering", "Selection",
           "SweepResult", "default_grid", "run_sweep", "seed_stability", "select_configuration",
           "subsample_stability", "read_assignments", "write_all", "write_assignments",
           "write_selection", "write_sweep"]

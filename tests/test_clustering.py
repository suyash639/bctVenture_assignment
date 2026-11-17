"""
Unit tests for src/clustering. ALL DATA HERE IS SYNTHETIC (fixed-seed Gaussian blobs and
hand-placed outliers); none of it represents real ads, and it is never used for analysis.

Run: .venv/bin/python -m pytest tests/test_clustering.py -q
"""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

try:
    import sklearn  # noqa: F401
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

if HAS_SKLEARN:
    from src.clustering import (
        ClusterConfig,
        compute_metrics,
        default_grid,
        read_assignments,
        run_clustering,
        run_sweep,
        select_configuration,
        write_all,
        write_assignments,
    )


def synthetic_blobs(n_per=15, centres=((0, 0), (10, 0), (5, 9)), sd=0.6, seed=0):
    """SYNTHETIC: well-separated Gaussian blobs with known ground-truth labels."""
    rng = np.random.default_rng(seed)
    X = np.vstack([np.asarray(c) + rng.normal(0, sd, (n_per, 2)) for c in centres])
    truth = np.repeat(np.arange(len(centres)), n_per)
    ids = [f"SYNTH_{i:03d}" for i in range(len(X))]
    return X, truth, ids


@unittest.skipUnless(HAS_SKLEARN, "scikit-learn not installed")
class TestClusteringSynthetic(unittest.TestCase):
    def test_synthetic_recovers_three_blobs(self):
        from sklearn.metrics import adjusted_rand_score
        X, truth, ids = synthetic_blobs()
        for cfg in (ClusterConfig("kmeans", {"n_clusters": 3}),
                    ClusterConfig("agglomerative", {"n_clusters": 3, "linkage": "ward"}),
                    ClusterConfig("hdbscan", {"min_cluster_size": 5})):
            r = run_clustering(X, ids, cfg)
            clean = r.labels >= 0
            self.assertEqual(r.metrics["n_clusters"], 3, cfg.config_id)
            self.assertGreater(adjusted_rand_score(truth[clean], r.labels[clean]), 0.95, cfg.config_id)
            self.assertGreater(r.metrics["silhouette"], 0.7)

    def test_synthetic_noise_is_labelled_not_forced(self):
        X, _, ids = synthetic_blobs()
        X = np.vstack([X, [[100, -100], [-100, 100]]])  # two isolated SYNTHETIC outliers
        ids = ids + ["SYNTH_OUT_1", "SYNTH_OUT_2"]
        r = run_clustering(X, ids, ClusterConfig("hdbscan", {"min_cluster_size": 5}))
        self.assertEqual(int(r.labels[-1]), -1)
        self.assertEqual(int(r.labels[-2]), -1)
        rows = {row["ad_id"]: row for row in r.to_assignments()}
        self.assertTrue(rows["SYNTH_OUT_1"]["is_noise"])
        self.assertIsNone(rows["SYNTH_OUT_1"]["distance_to_centroid"])
        self.assertEqual(r.metrics["n_noise"], 2)
        # metrics are computed on non-noise points only
        clean = compute_metrics(X[:-2], r.labels[:-2])
        self.assertAlmostEqual(clean["silhouette"], r.metrics["silhouette"], places=6)

    def test_synthetic_metrics_none_when_single_cluster(self):
        X, _, ids = synthetic_blobs(centres=((0, 0),), n_per=20)
        m = compute_metrics(X, np.zeros(len(X), dtype=int))
        self.assertIsNone(m["silhouette"])
        self.assertIsNone(m["davies_bouldin"])
        self.assertIsNone(m["calinski_harabasz"])
        self.assertIn("metrics_undefined_reason", m)
        m = compute_metrics(X, np.arange(len(X)))  # every point its own cluster
        self.assertIsNone(m["silhouette"])

    def test_synthetic_determinism_same_seed(self):
        X, _, ids = synthetic_blobs(sd=2.5)
        a = run_clustering(X, ids, ClusterConfig("kmeans", {"n_clusters": 4}, seed=7))
        b = run_clustering(X, ids, ClusterConfig("kmeans", {"n_clusters": 4}, seed=7))
        np.testing.assert_array_equal(a.labels, b.labels)
        self.assertEqual(a.metrics, b.metrics)
        self.assertEqual(ClusterConfig("kmeans", {"n_init": 10, "n_clusters": 4}).config_id,
                         ClusterConfig("kmeans", {"n_clusters": 4, "n_init": 10}).config_id)

    def test_synthetic_alignment_preserved_under_permutation(self):
        X, _, ids = synthetic_blobs()
        base = run_clustering(X, ids, ClusterConfig("agglomerative", {"n_clusters": 3, "linkage": "ward"}))
        perm = np.random.default_rng(3).permutation(len(ids))
        shuffled = run_clustering(X[perm], [ids[i] for i in perm],
                                  ClusterConfig("agglomerative", {"n_clusters": 3, "linkage": "ward"}))
        a = {i: int(lab) for i, lab in zip(base.ad_ids, base.labels)}
        b = {i: int(lab) for i, lab in zip(shuffled.ad_ids, shuffled.labels)}
        # same partition regardless of row order (label ids may be renamed)
        pairs = {(a[i], b[i]) for i in ids}
        self.assertEqual(len(pairs), 3)

    def test_input_validation(self):
        X, _, ids = synthetic_blobs()
        with self.assertRaises(ValueError):
            run_clustering(X, ids[:-1], ClusterConfig("kmeans", {"n_clusters": 3}))
        with self.assertRaises(ValueError):
            run_clustering(X, ids[:-1] + [ids[0]], ClusterConfig("kmeans", {"n_clusters": 3}))
        Xn = X.copy()
        Xn[4, 0] = np.nan
        with self.assertRaises(ValueError):
            run_clustering(Xn, ids, ClusterConfig("kmeans", {"n_clusters": 3}))
        with self.assertRaises(ValueError):
            ClusterConfig("dbscan")


@unittest.skipUnless(HAS_SKLEARN, "scikit-learn not installed")
class TestSweepAndSelectionSynthetic(unittest.TestCase):
    def test_synthetic_selection_not_argmax_silhouette_on_degenerate_case(self):
        """SYNTHETIC: 3 moderate blobs + 2 far outliers. Silhouette alone prefers k=2
        (45 vs 2 points); multi-criteria selection must not pick that degenerate split."""
        rng = np.random.default_rng(0)
        centres = np.array([[0, 0], [4, 0], [2, 3.5]])
        X = np.vstack([c + rng.normal(0, 0.9, (15, 2)) for c in centres] + [np.array([[40, 40], [41, 40]])])
        ids = [f"SYNTH_{i:03d}" for i in range(len(X))]
        sweep = run_sweep(SimpleNamespace(X=X, ad_ids=ids),
                          [ClusterConfig("kmeans", {"n_clusters": k}) for k in range(2, 7)], n_boot=5)
        sel = select_configuration(sweep)
        best_sil = max((e for e in sweep.entries), key=lambda e: e.result.metrics["silhouette"])
        self.assertEqual(best_sil.config.params["n_clusters"], 2)
        self.assertNotEqual(sel.config.config_id, best_sil.config.config_id)
        self.assertIn("was not chosen", sel.rationale)
        self.assertIn("largest cluster holds", sel.rationale)

    def test_synthetic_sweep_records_failures_and_stability(self):
        X, _, ids = synthetic_blobs(n_per=4)  # n = 12
        cfgs = default_grid(len(ids)) + [ClusterConfig("kmeans", {"n_clusters": 50})]
        sweep = run_sweep(SimpleNamespace(X=X, ad_ids=ids), cfgs, n_boot=3)
        failed = [e for e in sweep.entries if e.error]
        self.assertEqual([e.config.params.get("n_clusters") for e in failed], [50])
        k3 = sweep.get("kmeans|n_clusters=3,n_init=10")
        self.assertIsNotNone(k3.stability["seed_ari"])
        self.assertIsNotNone(k3.stability["subsample_ari"])
        self.assertIsNotNone(k3.stability["neighbour_ari"])
        ward = sweep.get("agglomerative|linkage=ward,n_clusters=3")
        self.assertIsNone(ward.stability["seed_ari"])  # deterministic: no fake 1.0
        self.assertTrue(any("HDBSCAN" in n for n in sweep.notes))
        sel = select_configuration(sweep)
        self.assertEqual(sel.config.params.get("n_clusters"), 3)
        self.assertTrue(any(r["status"] == "failed" for r in sel.table))

    def test_synthetic_no_eligible_configuration(self):
        X, _, ids = synthetic_blobs(centres=((0, 0),), n_per=10)
        sweep = run_sweep(SimpleNamespace(X=X, ad_ids=ids),
                          [ClusterConfig("hdbscan", {"min_cluster_size": 10})], n_boot=2)
        sel = select_configuration(sweep)
        self.assertIsNone(sel.config)
        self.assertIn("no eligible configuration", sel.warnings)


@unittest.skipUnless(HAS_SKLEARN, "scikit-learn not installed")
class TestWritersSynthetic(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_synthetic_assignments_one_row_per_id_including_noise(self):
        X, _, ids = synthetic_blobs()
        X = np.vstack([X, [[100, 100]]])
        ids = ids + ["SYNTH_OUT"]
        brands = {i: ("BrandA" if n % 2 else "BrandB") for n, i in enumerate(ids)}
        fm = SimpleNamespace(X=X, ad_ids=ids, brands=brands)
        sweep = run_sweep(fm, [ClusterConfig("hdbscan", {"min_cluster_size": 5}),
                               ClusterConfig("kmeans", {"n_clusters": 3})], n_boot=3)
        r = sweep.get("hdbscan|min_cluster_size=5").result
        p = write_assignments(r, self.tmp / "a.csv", sweep.brands)
        rows = read_assignments(p)
        self.assertEqual([x["ad_id"] for x in rows], ids)
        self.assertEqual(rows[-1]["cluster_id"], -1)
        self.assertTrue(rows[-1]["is_noise"])
        self.assertEqual(rows[0]["brand"], brands[ids[0]])
        paths = write_all(sweep, select_configuration(sweep), self.tmp / "out")
        sel = json.loads(paths["selection"].read_text())
        self.assertIn("rationale", sel)
        with open(paths["assignments"]) as f:
            self.assertEqual(len(list(csv.DictReader(f))), len(ids))
        sw = json.loads(paths["sweep"].read_text())
        self.assertEqual(sw["n_records"], len(ids))

    def test_synthetic_brands_from_records(self):
        X, _, ids = synthetic_blobs(n_per=4)
        recs = {i: {"dataset": {"brand": "SynthBrand"}} for i in ids}
        sweep = run_sweep(SimpleNamespace(X=X, ad_ids=ids, records=recs),
                          [ClusterConfig("kmeans", {"n_clusters": 3})], n_boot=2)
        self.assertEqual(set(sweep.brands.values()), {"SynthBrand"})


if __name__ == "__main__":
    unittest.main()

"""
Integration tests for src/pipeline.

The end-to-end test runs every stage on a small subset (10 rows) of REAL verified creatives
from data/processed/validated_dataset.csv, writing only to a temp dir. It checks the plumbing:
alignment, freeze guard, provisional routing, outputs. It produces no findings, and no
synthetic ads are used. Skips if the vision/ML stack or the verified assets are unavailable.

Run: .venv/bin/python -m pytest tests/test_pipeline.py -v
"""

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from config.settings import BASE_DIR

DATASET = BASE_DIR / "data/processed/validated_dataset.csv"

try:
    import matplotlib  # noqa: F401
    import open_clip  # noqa: F401
    import sklearn  # noqa: F401
    HAS_STACK = True
except ImportError:
    HAS_STACK = False


def verified_subset(n=10, brands=("Kapiva", "OZiva")):
    rows = list(csv.DictReader(open(DATASET, encoding="utf-8")))
    out = []
    for b in brands:
        out += [r for r in rows if r["final_status"] == "VERIFIED" and r["brand"] == b
                and (BASE_DIR / r["local_image_path"]).is_file()][: n // len(brands)]
    return rows[0].keys(), out


@unittest.skipUnless(HAS_STACK and DATASET.is_file(), "ML stack or validated dataset unavailable")
class TestPipelineEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cols, rows = verified_subset()
        if len(rows) < 8:
            raise unittest.SkipTest("not enough verified local creatives for the integration subset")
        cls.ids = [r["ad_id"] for r in rows]
        cls.ds = cls.tmp / "subset.csv"
        with open(cls.ds, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cols))
            w.writeheader()
            w.writerows(rows)
        cls.cfg = {
            "inputs": {"dataset_csv": str(cls.ds), "freeze_marker": str(cls.tmp / "FROZEN.json"),
                       "features_json": str(cls.tmp / "vf.json"), "embeddings_npy": str(cls.tmp / "emb.npy"),
                       "require": {"final_status": "VERIFIED"}},
            "extraction": {"enabled": True, "device": "cpu", "batch_size": 8},
            "features": {"blocks": {"clip": 1.0, "numeric": 0.0, "colour": 0.0, "layout": 0.0, "text": 0.0},
                         "clip_pca_components": None, "scaler": "standard", "impute": "median", "seed": 0},
            "feature_variants": {},
            "clustering": {"grid": [{"algorithm": "kmeans", "params": {"n_clusters": k, "n_init": 10}} for k in (2, 3)]
                           + [{"algorithm": "agglomerative", "params": {"n_clusters": 3, "linkage": "ward"}}],
                           "stability_seeds": [0, 1]},
            "analytics": {"representatives_per_cluster": 2},
            "intelligence": {"min_n": 3},
            "outputs": {"root": str(cls.tmp / "out"), "report": str(cls.tmp / "report.md")},
            "seed": 0,
        }
        cls.cfg_path = cls.tmp / "cfg.json"
        cls.cfg_path.write_text(json.dumps(cls.cfg))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def freeze(self):
        (self.tmp / "FROZEN.json").write_text(json.dumps(
            {"dataset_sha256": hashlib.sha256(self.ds.read_bytes()).hexdigest()}))

    def test_1_refuses_unfrozen_dataset(self):
        from src.pipeline.run import PipelineError, run
        (self.tmp / "FROZEN.json").unlink(missing_ok=True)
        with self.assertRaises(PipelineError) as cm:
            run(self.cfg_path, ["validate"])
        self.assertIn("not frozen", str(cm.exception))

    def test_2_stale_freeze_marker_refused(self):
        from src.pipeline.run import PipelineError, run
        (self.tmp / "FROZEN.json").write_text(json.dumps({"dataset_sha256": "0" * 64}))
        with self.assertRaises(PipelineError):
            run(self.cfg_path, ["validate"])

    def test_3_provisional_run_is_routed_and_labelled(self):
        from src.pipeline.run import run
        (self.tmp / "FROZEN.json").unlink(missing_ok=True)
        ctx = run(self.cfg_path, ["validate", "extract"], allow_provisional=True)
        self.assertTrue(ctx.provisional)
        self.assertEqual(ctx.out, self.tmp / "out" / "provisional")

    def test_4_full_run_frozen(self):
        from src.pipeline.run import run
        self.freeze()
        ctx = run(self.cfg_path)  # all stages
        self.assertFalse(ctx.provisional)
        out = self.tmp / "out"
        # features cover exactly the selected ids, in dataset order
        recs = json.loads((self.tmp / "vf.json").read_text())["records"]
        self.assertEqual([r["ad_id"] for r in recs], self.ids)
        # one assignment per ad
        rows = list(csv.DictReader(open(out / "clustering/clip/assignments.csv")))
        self.assertEqual(sorted(r["ad_id"] for r in rows), sorted(self.ids))
        self.assertTrue(all(r["brand"] in ("Kapiva", "OZiva") for r in rows), "brand column must be filled")
        # analytics + intelligence produced, all ids traceable
        man = json.loads((out / "analytics/clip/manifest.json").read_text())
        self.assertTrue(man)
        obs = json.loads((out / "intelligence/clip/observations.json").read_text())
        obs = obs.get("observations", obs) if isinstance(obs, dict) else obs
        for o in obs:
            self.assertTrue(set(o["supporting_ad_ids"]) <= set(self.ids), o["observation_id"])
        rm = json.loads((out / "run_manifest.json").read_text())
        self.assertFalse(rm["provisional"])
        self.assertEqual(rm["summary"]["dataset"]["n_selected"], len(self.ids))
        self.assertTrue((self.tmp / "report.md").is_file())


class TestFreezeCommand(unittest.TestCase):
    def test_refuses_without_integrity_report(self):
        from src.pipeline.freeze import check
        tmp = Path(tempfile.mkdtemp())
        try:
            ds = tmp / "d.csv"
            ds.write_text("ad_id,final_status\n1,EXCLUDED\n")
            problems = check(ds, tmp / "missing.json")
            self.assertTrue(any("integrity report missing" in p for p in problems))
            self.assertTrue(any("no VERIFIED rows" in p for p in problems))
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()

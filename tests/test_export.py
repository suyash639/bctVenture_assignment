"""
Dashboard export: truthfulness rules + cross-language contract check.

Uses a small subset of REAL verified creatives (no synthetic ads); outputs go to a temp dir.
The contract check runs the dashboard's own TypeScript validators (vitest) on the export.
"""
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from config.settings import BASE_DIR

try:
    import open_clip  # noqa: F401
    import sklearn  # noqa: F401
    HAS_STACK = True
except ImportError:
    HAS_STACK = False
DASH = BASE_DIR / "dashboard"
HAS_NODE = (DASH / "node_modules" / ".bin" / "vitest").exists()


@unittest.skipUnless(HAS_STACK and (BASE_DIR / "data/processed/validated_dataset.csv").is_file(), "stack/dataset unavailable")
class TestDashboardExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.test_pipeline import verified_subset
        cls.tmp = Path(tempfile.mkdtemp())
        cols, rows = verified_subset(8)
        cls.ids = [r["ad_id"] for r in rows]
        excluded = next(r for r in csv.DictReader(open(BASE_DIR / "data/processed/validated_dataset.csv"))
                        if r["final_status"] != "VERIFIED")
        cls.excluded_id = excluded["ad_id"]
        cls.ds = cls.tmp / "subset.csv"
        with open(cls.ds, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(cols))
            w.writeheader()
            w.writerows(rows + [excluded])
        cfg = json.loads((BASE_DIR / "config/analysis_pipeline.json").read_text())
        cfg["inputs"].update(dataset_csv=str(cls.ds), freeze_marker=str(cls.tmp / "FROZEN.json"),
                             features_json=str(cls.tmp / "vf.json"), embeddings_npy=str(cls.tmp / "emb.npy"))
        cfg["extraction"]["enabled"] = True
        cfg["feature_variants"] = {}
        cfg["clustering"] = {"grid": [{"algorithm": "kmeans", "params": {"n_clusters": 2, "n_init": 10}},
                                      {"algorithm": "kmeans", "params": {"n_clusters": 3, "n_init": 10}}],
                             "stability_seeds": [0, 1]}
        cfg["outputs"] = {"root": str(cls.tmp / "out"), "report": str(cls.tmp / "report.md")}
        cls.cfg = cls.tmp / "cfg.json"
        cls.cfg.write_text(json.dumps(cfg))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_1_unfrozen_export_is_provisional_and_hides_unrun_sections(self):
        from src.export.dashboard_data import export
        (self.tmp / "FROZEN.json").unlink(missing_ok=True)
        m = export(self.cfg, self.tmp / "export_prov")
        self.assertTrue(m["provisional"])
        self.assertEqual(m["available"], {"features": False, "clusters": False, "projection": False, "insights": False})
        ads = json.loads((self.tmp / "export_prov/ads.json").read_text())
        self.assertEqual([a["ad_id"] for a in ads], self.ids)          # VERIFIED only, dataset order
        self.assertNotIn(self.excluded_id, {a["ad_id"] for a in ads})   # excluded rows never exported
        self.assertTrue(all(a["features"] is None and a["cluster"] is None for a in ads))
        self.assertFalse((self.tmp / "export_prov/clusters.json").exists())

    def test_2_frozen_full_export_and_ts_contract(self):
        from src.export.dashboard_data import export
        from src.pipeline.run import run
        (self.tmp / "FROZEN.json").write_text(json.dumps({"dataset_sha256": hashlib.sha256(self.ds.read_bytes()).hexdigest()}))
        run(self.cfg)
        out = self.tmp / "export"
        m = export(self.cfg, out)
        self.assertFalse(m["provisional"])
        self.assertTrue(all(m["available"].values()), m["available"])
        ads = json.loads((out / "ads.json").read_text())
        for a in ads:
            src = BASE_DIR / next(r["local_image_path"] for r in csv.DictReader(open(self.ds)) if r["ad_id"] == a["ad_id"])
            self.assertEqual((out / a["image"].removeprefix("/data/")).read_bytes(), src.read_bytes())
        cl = json.loads((out / "clusters.json").read_text())
        self.assertEqual(sorted(x for c in cl["clusters"] for x in c["ad_ids"]), sorted(self.ids))
        self.assertNotIn("unknown", {b for c in cl["clusters"] for b in c["brand_mix"]})
        if HAS_NODE:
            r = subprocess.run(["npx", "vitest", "run", "tests/export_contract.test.ts"], cwd=DASH,
                               env={**__import__("os").environ, "EXPORT_DIR": str(out)}, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
            self.assertIn("4 passed", r.stdout)


if __name__ == "__main__":
    unittest.main()

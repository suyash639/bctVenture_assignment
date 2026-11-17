"""Regression tests for bugs found by the independent QA audit (reports/qa_audit.md)."""
import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from config.settings import BASE_DIR

DATASET = BASE_DIR / "data/processed/validated_dataset.csv"


class TestB3StatusParsing(unittest.TestCase):
    def test_status_is_active_inactive_line_not_first_line(self):
        from src.scraper.ad_library_cards import parse_card
        text = "Link to ad\n​\nActive\nLibrary ID: 123\nStarted running on 1 Oct 2026\nSee ad details\nMamaearth\nSponsored\nHi\nShop Now"
        self.assertEqual(parse_card(text, [])["status"], "Active")
        self.assertIsNone(parse_card("Link to ad\nLibrary ID: 5\n", [])["status"])

    @unittest.skipUnless(DATASET.is_file(), "dataset not built")
    def test_no_verified_row_has_non_status_value(self):
        rows = [r for r in csv.DictReader(open(DATASET)) if r["final_status"] == "VERIFIED"]
        self.assertTrue(all(r["status"] in ("Active", "Inactive") for r in rows),
                        {r["ad_id"]: r["status"] for r in rows if r["status"] not in ("Active", "Inactive")})


@unittest.skipUnless(DATASET.is_file(), "dataset not built")
class TestB2FreezeRecomputesIntegrity(unittest.TestCase):
    def test_tampered_copy_is_refused(self):
        from src.pipeline.freeze import check
        tmp = Path(tempfile.mkdtemp())
        try:
            rows = list(csv.DictReader(open(DATASET)))
            ver = [i for i, r in enumerate(rows) if r["final_status"] == "VERIFIED"]
            rows[ver[0]]["image_sha256"] = "0" * 64                                   # hash mismatch
            rows[ver[1]]["local_image_path"] = rows[ver[2]]["local_image_path"]       # shared image
            rows[ver[3]]["advertiser"] = "Nykaa"                                      # not allowlisted
            p = tmp / "d.csv"
            with open(p, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
            problems = " ".join(check(p, BASE_DIR / "data/quality/dataset_integrity_report.json"))
            self.assertIn("sha256 does not match", problems)
            self.assertIn("shared with", problems)
            self.assertIn("not an allowlisted official page", problems)
        finally:
            shutil.rmtree(tmp)

    def test_real_dataset_passes(self):
        from src.pipeline.freeze import check
        self.assertEqual(check(DATASET, BASE_DIR / "data/quality/dataset_integrity_report.json"), [])


@unittest.skipUnless(DATASET.is_file(), "dataset not built")
class TestB1B4Exporter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        rows = [r for r in csv.DictReader(open(DATASET)) if r["final_status"] == "VERIFIED"][:3]
        self.ds = self.tmp / "d.csv"
        with open(self.ds, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        self.ids = [r["ad_id"] for r in rows]
        sha = hashlib.sha256(self.ds.read_bytes()).hexdigest()
        (self.tmp / "FROZEN.json").write_text(json.dumps({"dataset_sha256": sha}))
        # a pipeline run + features recorded against a DIFFERENT dataset version (stale)
        out = self.tmp / "out"
        (out / "clustering/clip").mkdir(parents=True)
        (out / "run_manifest.json").write_text(json.dumps({"summary": {"dataset": {"sha256": "f" * 64}}}))
        with open(out / "clustering/clip/assignments.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ad_id", "brand", "cluster_id", "is_noise", "algorithm", "config_id", "distance_to_centroid", "membership_probability"])
            for a in self.ids:
                w.writerow([a, "", 0, False, "kmeans", "k", 0.1, ""])
        (self.tmp / "vf.json").write_text(json.dumps({"meta": {"selection": {"dataset_sha256": "f" * 64}},
                                                      "records": [{"ad_id": a, "extraction_status": "success"} for a in self.ids]}))
        cfg = json.loads((BASE_DIR / "config/analysis_pipeline.json").read_text())
        cfg["inputs"].update(dataset_csv=str(self.ds), freeze_marker=str(self.tmp / "FROZEN.json"),
                             features_json=str(self.tmp / "vf.json"), embeddings_npy=str(self.tmp / "e.npy"))
        cfg["outputs"]["root"] = str(out)
        self.cfg = self.tmp / "cfg.json"
        self.cfg.write_text(json.dumps(cfg))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_b1_stale_run_and_features_are_not_exported(self):
        from src.export.dashboard_data import export
        m = export(self.cfg, self.tmp / "export")
        self.assertFalse(m["provisional"])
        self.assertEqual(m["available"], {"features": False, "clusters": False, "projection": False, "insights": False})

    def test_b4_refuses_to_wipe_unrelated_directory(self):
        from src.export.dashboard_data import ExportError, export
        target = self.tmp / "notes"
        target.mkdir()
        (target / "notes.txt").write_text("keep me")
        with self.assertRaises(ExportError):
            export(self.cfg, target)
        self.assertTrue((target / "notes.txt").is_file())
        export(self.cfg, self.tmp / "export2")      # a previous export may be replaced
        export(self.cfg, self.tmp / "export2")


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for src/analytics. ALL DATA HERE IS SYNTHETIC: fake ad_ids ("SYN-xx"), random
vectors from a fixed seed and tiny generated images. None of it is a real ad.

Run: .venv/bin/python -m pytest tests/test_analytics.py -q -p no:cacheprovider
"""

import csv
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
from PIL import Image

from src.analytics import CoverageError, Manifest, generate_all, normalise_inputs, projections, select_representatives

BRANDS = ["SynBrandA", "SynBrandB", "SynBrandC"]


def synthetic_case(tmp: Path, n: int = 12, seed: int = 0):
    """SYNTHETIC bundle / fm / assignments with deliberate gaps:
    SYN-03 image file missing, SYN-05 not in feature matrix, SYN-07 null text_density,
    SYN-11 absent from assignments, SYN-09 and SYN-10 noise."""
    rng = np.random.default_rng(seed)
    ad_ids = [f"SYN-{i:02d}" for i in range(n)]
    records = {}
    for i, a in enumerate(ad_ids):
        img = tmp / f"{a}.png"
        if a != "SYN-03":
            Image.new("RGB", (60 + 10 * (i % 3), 80), tuple(int(x) for x in rng.integers(0, 255, 3))).save(img)
        w, h = (600, 600) if i % 3 == 0 else (338, 600) if i % 3 == 1 else (600, 314)
        records[a] = {"ad_id": a, "brand": BRANDS[i % 3], "image_path": str(img), "width": w, "height": h,
                      "aspect_ratio": round(w / h, 4), "orientation": ["square", "portrait", "landscape"][i % 3],
                      "text_density": None if a == "SYN-07" else round(float(rng.uniform(0, 0.4)), 4),
                      "layout_category": ["product_focused", "offer_heavy", "lifestyle", "unknown"][i % 4],
                      "dominant_colours": [{"hex": "#ff0000", "rgb": [255, 0, 0], "proportion": 0.6},
                                           {"hex": "#0000ff", "rgb": [0, 0, 255], "proportion": 0.4}],
                      "dataset": {"cta": "Shop Now"}}
    bundle = SimpleNamespace(ad_ids=ad_ids, records=records, embeddings=None)
    fm_ids = [a for a in ad_ids if a != "SYN-05"]
    X = rng.normal(size=(len(fm_ids), 6))
    fm = SimpleNamespace(X=X, ad_ids=fm_ids)
    assignments = []
    for i, a in enumerate(ad_ids):
        if a == "SYN-11":
            continue
        cid = -1 if a in ("SYN-09", "SYN-10") else i % 2
        assignments.append({"ad_id": a, "brand": BRANDS[i % 3], "cluster_id": str(cid),
                            "is_noise": str(cid == -1), "algorithm": "synthetic"})
    return bundle, fm, assignments


class AnalyticsCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bundle, self.fm, self.assign = synthetic_case(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestGenerateAllSynthetic(AnalyticsCase):
    def run_all(self, out="out"):
        return generate_all(self.bundle, self.fm, self.assign, out_dir=self.tmp / out, base_dir=self.tmp)

    def test_every_artefact_accounts_for_every_ad_id(self):
        man = self.run_all()
        universe = set(self.bundle.ad_ids)
        self.assertGreaterEqual(man["n_artefacts"], 12)
        for e in man["artefacts"]:
            accounted = set(e["ad_ids_covered"]) | {m["ad_id"] for m in e["missing"]}
            self.assertEqual(accounted, universe, e["path"] or e["kind"])
            for m in e["missing"]:
                self.assertTrue(m["reason"], f"missing without reason in {e['kind']}")

    def test_manifest_paths_exist_and_mappings_reference_ad_ids(self):
        out = self.tmp / "out"
        man = self.run_all()
        self.assertTrue((out / "manifest.json").exists())
        for e in man["artefacts"]:
            if e["status"] != "ok":
                continue
            self.assertTrue((out / e["path"]).exists(), e["path"])
            if e["mapping"]:
                with open(out / e["mapping"]) as f:
                    ids = {r["ad_id"] for r in csv.DictReader(f)}
                self.assertTrue(set(e["ad_ids_covered"]) <= ids | set(), e["mapping"])

    def test_missing_image_is_listed_not_dropped(self):
        man = self.run_all()
        self.assertIn("SYN-03", man["image_load_failures"])
        sheet = next(e for e in man["artefacts"] if e["kind"] == "contact_sheet"
                     and "SYN-03" in e["ad_ids_covered"])
        fail = [f for f in sheet["image_load_failures"] if f["ad_id"] == "SYN-03"]
        self.assertEqual(len(fail), 1)
        self.assertTrue(fail[0]["reason"])
        with open(self.tmp / "out" / sheet["mapping"]) as f:
            row = next(r for r in csv.DictReader(f) if r["ad_id"] == "SYN-03")
        self.assertEqual(row["image_loaded"], "False")

    def test_noise_and_unassigned_sheets_present(self):
        man = self.run_all()
        sheets = {e["cluster"]: e for e in man["artefacts"] if e["kind"] == "contact_sheet"}
        self.assertEqual(set(sheets), {"C0", "C1", "noise", "unassigned"})
        self.assertEqual(set(sheets["noise"]["ad_ids_covered"]), {"SYN-09", "SYN-10"})
        self.assertEqual(sheets["unassigned"]["ad_ids_covered"], ["SYN-11"])

    def test_null_features_and_matrix_exclusions_have_reasons(self):
        man = self.run_all()
        td = next(e for e in man["artefacts"] if e["kind"] == "text_density")
        self.assertEqual([m["ad_id"] for m in td["missing"]], ["SYN-07"])
        pca = next(e for e in man["artefacts"] if e["kind"] == "projection_pca")
        self.assertEqual([m["ad_id"] for m in pca["missing"]], ["SYN-05"])
        self.assertIn("feature matrix", pca["missing"][0]["reason"])

    def test_pca_reproducible(self):
        self.run_all("a")
        self.run_all("b")
        a = (self.tmp / "a/projections/pca_2d.csv").read_text()
        b = (self.tmp / "b/projections/pca_2d.csv").read_text()
        self.assertEqual(a, b)
        X = self.fm.X
        z1, _ = projections.pca_2d(X)
        z2, _ = projections.pca_2d(X.copy())
        np.testing.assert_array_equal(z1, z2)

    def test_umap_skipped_cleanly_when_absent(self):
        with mock.patch.object(projections, "umap_available", return_value=False):
            man = self.run_all("nou")
        u = next(e for e in man["artefacts"] if e["kind"] == "projection_umap")
        self.assertTrue(u["status"].startswith("skipped"))
        self.assertIsNone(u["path"])
        self.assertEqual(len(u["missing"]), len(self.bundle.ad_ids))

    def test_assignments_from_csv_path(self):
        p = self.tmp / "assignments.csv"
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, list(self.assign[0].keys()))
            w.writeheader()
            w.writerows(self.assign)
        man = generate_all(self.bundle, self.fm, p, out_dir=self.tmp / "csv", base_dir=self.tmp)
        self.assertEqual(man["clusters"]["noise"], 2)


class TestRepresentativesSynthetic(AnalyticsCase):
    def test_deterministic_and_closest_first(self):
        inp = normalise_inputs(self.bundle, self.assign)
        r1 = select_representatives(inp, self.fm, k=3)
        r2 = select_representatives(inp, self.fm, k=3)
        self.assertEqual(r1, r2)
        for lab, v in r1.items():
            d = [x["distance_to_centroid"] for x in v["representatives"]]
            self.assertEqual(d, sorted(d))
        self.assertNotIn("noise", r1)
        self.assertIn("SYN-05", r1["C1"]["not_in_matrix"])  # SYN-05 is cluster 1, excluded from fm

    def test_tie_break_by_ad_id(self):
        # SYNTHETIC: two points equidistant from the centroid
        bundle = SimpleNamespace(ad_ids=["SYN-b", "SYN-a"], records={"SYN-b": {"brand": "X"}, "SYN-a": {"brand": "X"}})
        fm = SimpleNamespace(X=np.array([[1.0, 0.0], [-1.0, 0.0]]), ad_ids=["SYN-b", "SYN-a"])
        inp = normalise_inputs(bundle, [{"ad_id": "SYN-b", "cluster_id": 0}, {"ad_id": "SYN-a", "cluster_id": 0}])
        reps = select_representatives(inp, fm, k=1)
        self.assertEqual(reps["C0"]["representatives"][0]["ad_id"], "SYN-a")


class TestManifestGuards(unittest.TestCase):
    def test_coverage_error_on_silent_omission(self):
        m = Manifest(["SYN-1", "SYN-2"], ".")
        with self.assertRaises(CoverageError):
            m.add("x.png", "k", "d", covered=["SYN-1"])
        with self.assertRaises(CoverageError):
            m.add("x.png", "k", "d", covered=["SYN-1", "SYN-2"], missing=[{"ad_id": "SYN-2", "reason": "r"}])
        m.add("x.png", "k", "d", covered=["SYN-1"], missing=[{"ad_id": "SYN-2", "reason": "r"}])

    def test_duplicate_assignment_rejected(self):
        b = SimpleNamespace(ad_ids=["SYN-1"], records={"SYN-1": {"brand": "X"}})
        with self.assertRaises(ValueError):
            normalise_inputs(b, [{"ad_id": "SYN-1", "cluster_id": 0}, {"ad_id": "SYN-1", "cluster_id": 1}])


if __name__ == "__main__":
    unittest.main()

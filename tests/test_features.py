"""
Tests for src/features. All records and vectors here are SYNTHETIC (fixed seeds, built in a
temp dir); they test mechanics only and are never used as analysis results.

Run: .venv/bin/python -m pytest tests/test_features.py -q -p no:cacheprovider
"""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.features import AlignmentError, FeatureMatrix, FusionConfig, build_feature_matrix, load_feature_bundle
from src.features.fusion import srgb_to_lab

DIM = 16


def synthetic_record(aid, i, **over):
    """SYNTHETIC feature record shaped like src/vision output."""
    r = {"ad_id": aid, "brand": "SyntheticBrand", "image_path": f"x/{aid}.jpg", "width": 600, "height": 600,
         "aspect_ratio": 1.0 + 0.1 * i, "orientation": ["square", "portrait", "landscape"][i % 3],
         "brightness": 0.3 + 0.05 * i, "contrast": 0.2 + 0.01 * i, "sharpness": 200.0 + 50 * i,
         "colourfulness": 20.0 + 3 * i,
         "dominant_colours": [{"hex": "#ff0000", "rgb": [255, 0, 0] if i % 2 else [0, 0, 255], "proportion": 0.5}],
         "colour_distribution": {k: (1.0 if k == ("red" if i % 2 else "blue") else 0.0) for k in
                                 ["white", "black", "grey", "red", "orange", "yellow", "yellow_green", "green",
                                  "green_cyan", "cyan", "azure", "blue", "violet", "magenta", "rose"]},
         "clip_embedding_reference": None, "ocr_text": "x", "ocr_n_text_regions": i, "text_density": 0.01 * i,
         "text_position": ["top", "middle", "bottom", "none"][i % 4],
         "layout_category": ["product_focused", "lifestyle", "offer_heavy"][i % 3],
         "extraction_status": "success", "extraction_error": None}
    r.update(over)
    return r


class SyntheticCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.rng = np.random.default_rng(0)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, records, emb, row_ids, dataset_rows=None):
        fj, fn = self.tmp / "vf.json", self.tmp / "emb.npy"
        fj.write_text(json.dumps({"meta": {"clip": {"row_ad_ids": row_ids, "embedding_dim": DIM}},
                                  "records": records}))
        np.save(fn, emb)
        ds = None
        if dataset_rows is not None:
            ds = self.tmp / "ds.csv"
            with open(ds, "w", newline="") as f:
                w = csv.DictWriter(f, ["ad_id", "brand", "final_status", "cta"])
                w.writeheader()
                w.writerows(dataset_rows)
        return fj, fn, ds

    def make(self, n=6, dataset=False, **kw):
        """SYNTHETIC: n records, all embedded with unit vectors."""
        ids = [f"10{i}" for i in range(n)]
        recs = [synthetic_record(a, i) for i, a in enumerate(ids)]
        emb = self.rng.normal(size=(n, DIM)).astype(np.float32)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        for i, r in enumerate(recs):
            r["clip_embedding_reference"] = {"file": "emb.npy", "row": i}
        rows = [{"ad_id": a, "brand": "SyntheticBrand", "final_status": "VERIFIED", "cta": "Shop now"} for a in ids]
        return recs, emb, ids, rows


class TestLoadValidation(SyntheticCase):
    def test_synthetic_clean_load(self):
        recs, emb, ids, _ = self.make()
        b = load_feature_bundle(*self.write(recs, emb, ids)[:2])
        self.assertEqual(b.ad_ids, ids)
        self.assertEqual(b.embeddings.shape, (6, DIM))
        np.testing.assert_allclose(b.embeddings, emb, atol=1e-6)
        self.assertEqual(b.excluded, [])

    def test_synthetic_alignment_mismatch_raises(self):
        recs, emb, ids, _ = self.make()
        swapped = ids[:]
        swapped[0], swapped[1] = swapped[1], swapped[0]  # meta order disagrees with record refs
        with self.assertRaises(AlignmentError):
            load_feature_bundle(*self.write(recs, emb, swapped)[:2])
        with self.assertRaises(AlignmentError):  # row count mismatch
            load_feature_bundle(*self.write(recs, emb[:5], ids)[:2])
        recs2 = [dict(r) for r in recs]
        recs2[2]["clip_embedding_reference"] = None  # row 2 now unreferenced
        with self.assertRaises(AlignmentError):
            load_feature_bundle(*self.write(recs2, emb, ids)[:2])

    def test_synthetic_bad_ids_raise(self):
        recs, emb, ids, _ = self.make()
        recs[1]["ad_id"] = recs[0]["ad_id"]
        with self.assertRaises(AlignmentError):
            load_feature_bundle(*self.write(recs, emb, ids)[:2])
        recs, emb, ids, _ = self.make()
        recs[0]["ad_id"] = 100
        with self.assertRaises(AlignmentError):
            load_feature_bundle(*self.write(recs, emb, ids)[:2])

    def test_synthetic_norm_checks(self):
        recs, emb, ids, _ = self.make()
        emb[0] *= 1.0005    # within 1e-3: re-normalised + issue
        emb[1] *= 2.0       # way off: unavailable + issue
        emb[2, 0] = np.nan  # non-finite
        b = load_feature_bundle(*self.write(recs, emb, ids)[:2])
        self.assertAlmostEqual(float(np.linalg.norm(b.embeddings[0])), 1.0, places=5)
        self.assertTrue(np.isnan(b.embeddings[1]).all())
        self.assertTrue(np.isnan(b.embeddings[2]).all())
        probs = {(i["ad_id"], i["problem"].split()[0]) for i in b.issues if i["field"] == "clip_embedding"}
        self.assertIn((ids[0], "norm"), probs)
        self.assertIn((ids[1], "norm"), probs)
        self.assertIn((ids[2], "non-finite"), probs)
        fm = build_feature_matrix(b)  # clip active -> 1 and 2 excluded with reasons
        self.assertEqual(fm.ad_ids, [ids[0]] + ids[3:])
        self.assertEqual({e[0] for e in fm.excluded}, {ids[1], ids[2]})

    def test_synthetic_failed_records_excluded(self):
        recs, emb, ids, _ = self.make()
        recs[3]["extraction_status"], recs[3]["extraction_error"] = "failed", "unreadable"
        b = load_feature_bundle(*self.write(recs, emb, ids)[:2])
        self.assertNotIn(ids[3], b.ad_ids)
        self.assertIn((ids[3], "feature extraction failed: unreadable"), b.excluded)

    def test_synthetic_dataset_status_filter(self):
        recs, emb, ids, rows = self.make()
        rows[0]["final_status"] = "EXCLUDED"
        del rows[1]                                   # feature record without dataset row
        rows.append({"ad_id": "999", "brand": "SyntheticBrand", "final_status": "VERIFIED", "cta": ""})
        fj, fn, ds = self.write(recs, emb, ids, rows)
        b = load_feature_bundle(fj, fn, ds, {"final_status": "VERIFIED"})
        self.assertEqual(b.ad_ids, ids[2:])
        reasons = dict(b.excluded)
        self.assertIn("final_status=EXCLUDED", reasons[ids[0]])
        self.assertEqual(reasons[ids[1]], "not present in dataset")
        self.assertEqual(reasons["999"], "passes dataset filter but has no feature record")
        self.assertEqual(b.records[ids[2]]["dataset"]["cta"], "Shop now")


class TestFusion(SyntheticCase):
    def bundle(self, recs=None):
        r, emb, ids, _ = self.make()
        return load_feature_bundle(*self.write(recs or r, emb, ids)[:2])

    def test_synthetic_default_is_clip_only_centred(self):
        b = self.bundle()
        fm = build_feature_matrix(b)
        self.assertEqual(list(fm.blocks), ["clip"])
        self.assertEqual(fm.X.shape, (6, DIM))
        np.testing.assert_allclose(fm.X.mean(axis=0), 0, atol=1e-9)
        self.assertAlmostEqual(float(np.mean(np.sum(fm.X ** 2, axis=1))), 1.0, places=6)

    def test_synthetic_missing_values_median_vs_drop(self):
        recs, emb, ids, _ = self.make()
        recs[0]["brightness"] = None
        b = load_feature_bundle(*self.write(recs, emb, ids)[:2])
        self.assertIn({"ad_id": ids[0], "field": "brightness", "problem": "missing"}, b.issues)
        cfg = FusionConfig(blocks={"clip": 1.0, "numeric": 1.0})
        fm = build_feature_matrix(b, cfg)
        self.assertEqual(len(fm.ad_ids), 6)
        self.assertTrue(np.isfinite(fm.X).all())
        self.assertTrue(any(i["field"] == "numeric.brightness" for i in fm.issues))
        fm2 = build_feature_matrix(b, FusionConfig(blocks={"clip": 1.0, "numeric": 1.0}, impute="drop"))
        self.assertEqual(fm2.ad_ids, ids[1:])
        self.assertEqual(fm2.excluded, [(ids[0], "missing numeric.brightness (impute=drop)")])

    def test_synthetic_block_balance_and_weights(self):
        b = self.bundle()
        fm = build_feature_matrix(b, FusionConfig(blocks={"clip": 1.0, "numeric": 1.0, "colour": 1.0, "layout": 1.0}))
        for name, sl in fm.blocks.items():  # each block contributes mean squared norm 1 at weight 1
            self.assertAlmostEqual(float(np.mean(np.sum(fm.X[:, sl] ** 2, axis=1))), 1.0, places=6, msg=name)
        fm2 = build_feature_matrix(b, FusionConfig(blocks={"clip": 1.0, "numeric": 2.0}))
        self.assertAlmostEqual(float(np.mean(np.sum(fm2.X[:, fm2.blocks["numeric"]] ** 2, axis=1))), 4.0, places=6)
        self.assertEqual(len(fm.feature_names), fm.X.shape[1])

    def test_synthetic_pca_and_determinism(self):
        b = self.bundle()
        cfg = FusionConfig(blocks={"clip": 1.0, "layout": 0.5}, clip_pca_components=3, seed=7)
        a, c = build_feature_matrix(b, cfg), build_feature_matrix(b, FusionConfig.from_dict(cfg.to_dict()))
        self.assertEqual(a.blocks["clip"], slice(0, 3))
        np.testing.assert_array_equal(a.X, c.X)
        json.dumps(cfg.to_dict())  # JSON-serialisable

    def test_synthetic_save_load_roundtrip(self):
        fm = build_feature_matrix(self.bundle(), FusionConfig(blocks={"clip": 1.0, "colour": 1.0}))
        fm.save(self.tmp / "fm")
        back = FeatureMatrix.load(self.tmp / "fm")
        np.testing.assert_array_equal(back.X, fm.X)
        self.assertEqual((back.ad_ids, back.feature_names, back.blocks, back.config),
                         (fm.ad_ids, fm.feature_names, fm.blocks, fm.config))

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            FusionConfig(blocks={"clip": 0.0}).validate()
        with self.assertRaises(ValueError):
            FusionConfig(blocks={"pixels": 1.0}).validate()
        with self.assertRaises(NotImplementedError):
            FusionConfig(blocks={"clip": 1.0, "text": 1.0}).validate()

    def test_lab_reference_values(self):
        np.testing.assert_allclose(srgb_to_lab([255, 255, 255]), [100, 0, 0], atol=0.05)
        np.testing.assert_allclose(srgb_to_lab([255, 0, 0]), [53.24, 80.09, 67.20], atol=0.05)


if __name__ == "__main__":
    unittest.main()


class TestRealVisionOutputs(unittest.TestCase):
    """Mechanics check on real vision-pipeline outputs for 3 verified local creatives
    (not an analysis result). Skips if files or CLIP weights are unavailable."""

    def test_real_pipeline_output_loads_and_fuses(self):
        root = Path(__file__).resolve().parents[1]
        files = sorted((root / "data/creatives/verified/kapiva").glob("*.jpg"))[:3]
        if len(files) < 3:
            self.skipTest("verified creatives not present")
        try:
            from src.vision.clip_embeddings import ClipEmbedder
            ClipEmbedder(device="cpu").load()
        except Exception as e:  # torch missing / weights unavailable
            self.skipTest(f"CLIP unavailable: {e}")
        from src.vision.feature_pipeline import run
        from src.vision.preprocessing import ImageRecord
        tmp = Path(tempfile.mkdtemp())
        try:
            recs = [ImageRecord(p.stem, "Kapiva", p) for p in files]
            run(recs, tmp / "vf.json", tmp / "emb.npy", use_clip=True, use_ocr=False, device="cpu", verbose=False)
            b = load_feature_bundle(tmp / "vf.json", tmp / "emb.npy")
            self.assertEqual(b.ad_ids, [p.stem for p in files])
            fm = build_feature_matrix(b, FusionConfig(blocks={"clip": 1.0, "numeric": 0.5, "colour": 0.5, "layout": 0.5}))
            self.assertEqual(fm.ad_ids, b.ad_ids)
            self.assertTrue(np.isfinite(fm.X).all())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

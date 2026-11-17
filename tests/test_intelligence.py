"""
Tests for src/intelligence. ALL records and vectors here are SYNTHETIC (fixed-seed, clearly fake
brands "BrandA/BrandB/BrandC"); they test logic only and are never analysis results.

Run: .venv/bin/python -m pytest tests/test_intelligence.py -q -p no:cacheprovider
"""

import csv
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.intelligence import (
    BANNED_TERMS,
    IntelligenceConfig,
    Observation,
    build_observations,
    check_statements,
    fmt,
    load_assignments,
    normalise_cta,
)

COLOUR_KEYS = ["white", "black", "grey", "red", "orange", "yellow", "yellow_green", "green",
               "green_cyan", "cyan", "azure", "blue", "violet", "magenta", "rose"]


def synthetic_bundle(seed=0, n_per_brand=(5, 4, 2)):
    """SYNTHETIC: three fake brands with controlled features."""
    rng = np.random.default_rng(seed)
    ad_ids, records, emb = [], {}, []
    layouts = ["product_focused", "lifestyle", "offer_heavy", "educational", "unknown"]
    ctas = ["Shop Now", "shop now", "SHOP  NOW", "Learn more", None]
    base = {"BrandA": 0, "BrandB": 1, "BrandC": 2}
    for brand, n in zip(base, n_per_brand):
        centre = np.zeros(16)
        centre[base[brand] * 5] = 1.0
        for i in range(n):
            aid = f"SYN{base[brand]}{i:02d}"
            cd = {k: 0.0 for k in COLOUR_KEYS}
            cd["white"] = 0.6 if brand == "BrandA" else 0.1
            cd["green" if brand != "BrandC" else "blue"] = 1.0 - cd["white"]
            records[aid] = {
                "ad_id": aid, "brand": brand,
                "layout_category": "product_focused" if brand == "BrandA" and i < 4 else layouts[i % len(layouts)],
                "layout_reasons": ["rule"] if i % 2 == 0 else [],
                "orientation": "square" if brand != "BrandB" else "portrait",
                "aspect_ratio": 1.0 if brand != "BrandB" else 0.8,
                "text_density": [0.02, 0.10, 0.20, 0.30, 0.04][i % 5],
                "brightness": 0.5 + 0.05 * i, "contrast": 0.2, "sharpness": 300.0 + 10 * i, "colourfulness": 30.0,
                "colour_distribution": cd,
                "ocr_text": "FLAT 30% OFF ₹499" if i % 2 == 0 else "Pure herbal goodness",
                "ocr_n_text_regions": 10, "ocr_n_readable_regions": 3 if i == 1 else 9,
                "dataset": {"brand": brand, "cta": ctas[i % len(ctas)],
                            "advertiser": f"Creator{i} with {brand}" if i == 0 else brand,
                            "advertiser_type": "partnership" if i == 0 else "brand_page",
                            "image_type": "video_thumbnail" if (brand == "BrandB" and i == 0) else "static"},
            }
            v = centre + 0.05 * rng.standard_normal(16)
            emb.append(v / np.linalg.norm(v))
            ad_ids.append(aid)
    return {"ad_ids": ad_ids, "records": records, "embeddings": np.array(emb)}


def synthetic_assignments(bundle):
    rows = []
    for k, a in enumerate(bundle["ad_ids"]):
        brand = bundle["records"][a]["brand"]
        cid = {"BrandA": 0, "BrandB": 1, "BrandC": 1}[brand]
        if k == len(bundle["ad_ids"]) - 1:
            cid = -1
        rows.append({"ad_id": a, "brand": brand, "cluster_id": cid, "is_noise": cid == -1,
                     "distance_to_centroid": 0.1 * k})
    return rows


class TestHelpers(unittest.TestCase):
    def test_cta_normalisation(self):
        self.assertEqual(normalise_cta("Shop now"), "Shop Now")
        self.assertEqual(normalise_cta("  SHOP   NOW "), "Shop Now")
        self.assertEqual(normalise_cta(None), "No CTA")
        self.assertEqual(normalise_cta(""), "No CTA")

    def test_load_assignments_csv_and_noise(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            p = tmp / "a.csv"
            with open(p, "w", newline="") as f:
                w = csv.DictWriter(f, ["ad_id", "cluster_id", "is_noise"])
                w.writeheader()
                w.writerow({"ad_id": "1", "cluster_id": "0", "is_noise": "False"})
                w.writerow({"ad_id": "2", "cluster_id": "-1", "is_noise": "True"})
            a = load_assignments(p)
            self.assertEqual(a["1"]["cluster_id"], 0)
            self.assertFalse(a["1"]["is_noise"])
            self.assertTrue(a["2"]["is_noise"])
        finally:
            shutil.rmtree(tmp)

    def test_banned_terms_guard(self):
        bad = Observation("x", "dataset", "This layout performs well", "m", 1.0, "num", None, 5, ["a"], "m", [])
        with self.assertRaises(ValueError):
            check_statements([bad])


class TestObservationsSynthetic(unittest.TestCase):
    """SYNTHETIC data: checks traceability, numeric consistency, guards and determinism."""

    @classmethod
    def setUpClass(cls):
        cls.bundle = synthetic_bundle()
        cls.assign = synthetic_assignments(cls.bundle)
        cls.obs = build_observations(cls.bundle, cls.assign)
        cls.by_id = {o.observation_id: o for o in cls.obs}

    def test_every_observation_traceable(self):
        ids = set(self.bundle["ad_ids"])
        self.assertGreater(len(self.obs), 20)
        for o in self.obs:
            self.assertTrue(o.supporting_ad_ids, o.observation_id)
            self.assertTrue(set(o.supporting_ad_ids) <= ids, o.observation_id)
            self.assertTrue(o.method and o.metric and o.caveats, o.observation_id)
        self.assertEqual(len(self.by_id), len(self.obs), "observation ids must be unique")

    def test_statement_numbers_match_values(self):
        for o in self.obs:
            if o.value is not None:
                self.assertIn(fmt(o.value, o.value_format), o.statement, o.observation_id)
            if o.comparison and isinstance(o.comparison.get("value"), float) and "baseline" in o.comparison \
                    and o.value_format in ("pct", "num") and not o.observation_id.startswith("cross_brand_pair"):
                self.assertIn(fmt(o.comparison["value"], o.value_format), o.statement, o.observation_id)

    def test_known_values(self):
        # BrandA: 5 ads, ids 0-3 product_focused -> 80%
        o = self.by_id["layout:BrandA:product_focused"]
        self.assertAlmostEqual(o.value, 0.8)
        self.assertEqual(o.n, 5)
        self.assertEqual(o.supporting_ad_ids, ["SYN000", "SYN001", "SYN002", "SYN003"])
        # CTA normalisation merges "Shop Now"/"shop now"/"SHOP  NOW": BrandA has i=0,1,2 -> 3/5
        c = self.by_id["cta:BrandA:Shop Now"]
        self.assertAlmostEqual(c.value, 0.6)
        # text density median BrandA = median(0.02,0.10,0.20,0.30,0.04) = 0.10
        self.assertAlmostEqual(self.by_id["text_density_median:BrandA"].value, 0.10)
        # high-text (>=0.15): 0.20, 0.30 -> 2/5
        self.assertAlmostEqual(self.by_id["text_density_high:BrandA"].value, 0.4)
        # white-dominant: BrandA white=0.6 for all
        self.assertAlmostEqual(self.by_id["white_dominant:BrandA"].value, 1.0)
        # orientation BrandB portrait 100%
        self.assertAlmostEqual(self.by_id["orientation:BrandB:portrait"].value, 1.0)
        # offer wording on even indices: BrandA i=0,2,4 -> 3/5
        self.assertAlmostEqual(self.by_id["offer_text:BrandA"].value, 0.6)
        # video poster: 1 of 11
        self.assertAlmostEqual(self.by_id["format_mix:dataset"].value, 1 / 11, places=5)

    def test_min_n_guard(self):
        # BrandC has 2 ads (product_focused, lifestyle): tie broken alphabetically -> lifestyle
        o = self.by_id["layout:BrandC:lifestyle"]
        self.assertEqual(o.n, 2)
        self.assertEqual(o.status, "insufficient_data")
        self.assertTrue(o.statement.startswith("Insufficient data"))
        self.assertEqual(self.by_id["layout:BrandA:product_focused"].status, "ok")
        strict = build_observations(self.bundle, self.assign, config=IntelligenceConfig(min_n=6))
        self.assertEqual({o.status for o in strict if o.scope == "brand:BrandA" and o.observation_id.startswith("layout")},
                         {"insufficient_data"})

    def test_clip_consistency_intra_exceeds_inter_on_separated_synthetic_brands(self):
        o = self.by_id["clip_consistency:BrandA"]
        self.assertGreater(o.value, o.comparison["value"])
        self.assertEqual(o.details["n_intra_pairs"], 10)

    def test_cross_brand_pairs_are_cross_brand(self):
        pairs = [o for o in self.obs if o.observation_id.startswith("cross_brand_pair")]
        self.assertEqual(len(pairs), 5)
        for o in pairs:
            a, b = o.supporting_ad_ids
            self.assertNotEqual(self.bundle["records"][a]["brand"], self.bundle["records"][b]["brand"])
        self.assertEqual([o.value for o in pairs], sorted([o.value for o in pairs], reverse=True))

    def test_cluster_profiles_and_noise(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            build_observations(self.bundle, self.assign, out_dir=tmp)
            prof = json.loads((tmp / "cluster_profiles.json").read_text())["profiles"]
            self.assertEqual(set(prof), {"0", "1", "noise"})
            self.assertEqual(prof["noise"]["size"], 1)
            self.assertEqual(sum(p["size"] for p in prof.values()), len(self.bundle["ad_ids"]))
            self.assertEqual(prof["1"]["brand_mix"], {"BrandB": 4, "BrandC": 1})
            for p in prof.values():
                self.assertTrue(set(p["representative_ad_ids"]) <= set(p["ad_ids"]))
            self.assertIn("mixed_cluster:1", self.by_id)
            self.assertIn("noise:dataset", self.by_id)
            data = json.loads((tmp / "observations.json").read_text())
            self.assertEqual(len(data["observations"]), len(self.obs))
            md = (tmp / "observations.md").read_text()
            self.assertIn("Cluster profiles", md)
        finally:
            shutil.rmtree(tmp)

    def test_distinguishing_features_z_scores(self):
        feats = [o for o in self.obs if o.observation_id.startswith("cluster_feature:0:")]
        self.assertTrue(feats)
        for o in feats:
            self.assertIn(f"z = {o.comparison['z']:+.2f}", o.statement)

    def test_no_banned_terms_anywhere_in_statements(self):
        for o in self.obs:
            for t in BANNED_TERMS:
                self.assertIsNone(re.search(rf"\b{re.escape(t)}\b", o.statement.lower()), (o.observation_id, t))

    def test_deterministic(self):
        again = build_observations(synthetic_bundle(), synthetic_assignments(synthetic_bundle()))
        self.assertEqual([o.to_dict() for o in again], [o.to_dict() for o in self.obs])

    def test_works_without_embeddings_or_assignments(self):
        b = synthetic_bundle()
        b.pop("embeddings")
        obs = build_observations(b)
        self.assertFalse([o for o in obs if o.scope.startswith("cluster") or o.observation_id.startswith("clip")])
        self.assertTrue(obs)

    def test_missing_features_are_skipped_not_invented(self):
        b = synthetic_bundle()
        b["records"]["SYN000"]["text_density"] = None
        b["records"]["SYN000"]["colour_distribution"] = None
        obs = {o.observation_id: o for o in build_observations(b)}
        o = obs["text_density_median:BrandA"]
        self.assertEqual(o.n, 4)
        self.assertNotIn("SYN000", o.supporting_ad_ids)
        self.assertEqual(obs["white_dominant:BrandA"].n, 4)

    def test_embedding_row_mismatch_rejected(self):
        b = synthetic_bundle()
        b["embeddings"] = b["embeddings"][:-1]
        with self.assertRaises(ValueError):
            build_observations(b)


if __name__ == "__main__":
    unittest.main()

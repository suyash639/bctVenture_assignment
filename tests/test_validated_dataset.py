"""
Invariants of the validated dataset (data/processed/validated_dataset.csv).

These guard the acceptance rules: any VERIFIED record must satisfy all of them,
whatever the current record count is.
"""
import csv
import hashlib
import json
import unittest

from config.settings import BASE_DIR, OFFICIAL_ADVERTISERS, TARGET_BRANDS

DATASET = BASE_DIR / "data/processed/validated_dataset.csv"
INTEGRITY = BASE_DIR / "data/quality/dataset_integrity_report.json"
ACCEPT = {"advertiser_verification_status": {"VERIFIED"}, "image_verification_status": {"VERIFIED"},
          "metadata_verification_status": {"VERIFIED"}, "image_quality_status": {"PASS"},
          "duplicate_status": {"UNIQUE", "GROUP_REPRESENTATIVE", "NEAR_DUPLICATE_KEPT"}}


@unittest.skipUnless(DATASET.is_file(), "validated dataset not built yet")
class TestValidatedDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(csv.DictReader(open(DATASET, encoding="utf-8")))
        cls.ver = [r for r in cls.rows if r["final_status"] == "VERIFIED"]

    def test_unique_ids_and_canonical_brands(self):
        ids = [r["ad_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({r["brand"] for r in self.rows} <= set(TARGET_BRANDS))
        self.assertNotIn("Himalaya", {r["brand"] for r in self.rows})  # consolidated into Himalaya Wellness

    def test_verified_rows_pass_every_acceptance_check(self):
        for r in self.ver:
            for k, ok in ACCEPT.items():
                self.assertIn(r[k], ok, f"{r['ad_id']} {k}={r[k]}")

    def test_verified_advertiser_is_official_or_partnership(self):
        for r in self.ver:
            official = OFFICIAL_ADVERTISERS[r["brand"]]
            adv = r["advertiser"]
            ok = adv in official or (" with " in adv and adv.rsplit(" with ", 1)[1] in official)
            self.assertTrue(ok, f"{r['ad_id']}: {adv}")

    def test_verified_images_exist_and_hash_matches(self):
        for r in self.ver:
            p = BASE_DIR / r["local_image_path"]
            self.assertTrue(p.is_file(), r["ad_id"])
            self.assertTrue(r["local_image_path"].startswith("data/creatives/verified/"))
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), r["image_sha256"], r["ad_id"])

    def test_no_shared_image_between_verified_ads(self):
        shas = [r["image_sha256"] for r in self.ver]
        self.assertEqual(len(shas), len(set(shas)))

    def test_excluded_rows_have_reasons(self):
        for r in self.rows:
            if r["final_status"] != "VERIFIED":
                self.assertTrue(r["exclusion_reasons"], r["ad_id"])

    def test_integrity_report_passed(self):
        self.assertTrue(json.loads(INTEGRITY.read_text())["passed"])


if __name__ == "__main__":
    unittest.main()

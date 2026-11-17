"""LEGACY — not collected by pytest (see legacy/README.md)."""
"""
Test suite for dataset schema and data integrity across all 50 ad records.
"""

import csv
import json
import unittest
from pathlib import Path

from config.settings import PROCESSED_DATA_DIR, RAW_DATA_DIR, TARGET_BRANDS


class TestDatasetIntegrity(unittest.TestCase):
    def setUp(self):
        self.master_json_path = PROCESSED_DATA_DIR / "all_brands_ads.json"
        self.master_csv_path = PROCESSED_DATA_DIR / "all_brands_ads.csv"

    def test_processed_files_exist(self):
        self.assertTrue(self.master_json_path.exists(), "Master JSON dataset must exist")
        self.assertTrue(self.master_csv_path.exists(), "Master CSV dataset must exist")

    def test_master_json_structure(self):
        with open(self.master_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("meta", data)
        self.assertIn("ads", data)
        ads = data["ads"]
        self.assertEqual(len(ads), 50, "Expected exactly 50 ad records in master dataset")

        # Verify brand distribution (10 per brand)
        brand_counts = {}
        for ad in ads:
            b = ad.get("brand_name")
            brand_counts[b] = brand_counts.get(b, 0) + 1

        for expected_brand in TARGET_BRANDS:
            self.assertEqual(
                brand_counts.get(expected_brand), 10,
                f"Brand '{expected_brand}' must have exactly 10 ad records"
            )

    def test_required_fields_present(self):
        with open(self.master_json_path, "r", encoding="utf-8") as f:
            ads = json.load(f)["ads"]

        required_non_null = ["brand_name", "ad_library_id", "creative_format", "status"]
        for i, ad in enumerate(ads):
            for field in required_non_null:
                self.assertIsNotNone(
                    ad.get(field),
                    f"Record #{i} (ID: {ad.get('ad_library_id')}) missing non-null field '{field}'"
                )
            self.assertEqual(
                ad.get("image_download_status"), "success",
                f"Record #{i} (ID: {ad.get('ad_library_id')}) must have image_download_status 'success'"
            )
            self.assertIsNotNone(
                ad.get("local_image_path"),
                f"Record #{i} (ID: {ad.get('ad_library_id')}) must have local_image_path"
            )

    def test_csv_matches_json(self):
        with open(self.master_csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 50, "CSV must contain exactly 50 rows")
        with open(self.master_json_path, "r", encoding="utf-8") as f:
            json_ads = json.load(f)["ads"]

        for csv_row, json_ad in zip(reader, json_ads):
            self.assertEqual(csv_row["ad_library_id"], str(json_ad["ad_library_id"]))
            self.assertEqual(csv_row["brand_name"], json_ad["brand_name"])


if __name__ == "__main__":
    unittest.main()


"""LEGACY — not collected by pytest (see legacy/README.md)."""
"""
Test suite for creative images integrity on disk (50/50 valid PNGs).
"""

import unittest
from pathlib import Path

from config.settings import CREATIVES_DIR, TARGET_BRANDS
from src.utils.image_validator import inspect_png_header, validate_creative_images


class TestCreativesIntegrity(unittest.TestCase):
    def test_all_50_images_valid(self):
        results = validate_creative_images(CREATIVES_DIR)
        self.assertEqual(results["total_files"], 50, "Total creative images on disk must be 50")
        self.assertEqual(results["total_valid"], 50, "All 50 creative images must be valid PNGs")
        self.assertEqual(results["total_corrupt"], 0, "No creative images may be corrupt")

    def test_each_brand_has_10_valid_images(self):
        for brand, meta in TARGET_BRANDS.items():
            slug = meta["slug"]
            brand_dir = CREATIVES_DIR / slug
            self.assertTrue(brand_dir.exists(), f"Directory for {brand} ({slug}) must exist")
            pngs = list(brand_dir.glob("*.png"))
            self.assertEqual(len(pngs), 10, f"Brand {brand} must have exactly 10 PNGs")

            for p in pngs:
                is_valid, size, w, h = inspect_png_header(p)
                self.assertTrue(is_valid, f"File {p} must be a valid PNG")
                self.assertGreater(size, 5000, f"File {p} size must exceed 5KB")
                self.assertGreater(w, 50, f"File {p} width must exceed 50px")
                self.assertGreater(h, 50, f"File {p} height must exceed 50px")


if __name__ == "__main__":
    unittest.main()


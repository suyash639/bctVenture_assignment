"""
Test suite for scraper helper functions and configuration settings.
"""

import unittest

from config.settings import (
    BASE_DIR,
    CREATIVES_DIR,
    DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    TARGET_BRANDS,
)
from src.scraper.ad_library_scraper import build_search_url
from src.scraper.extraction import decode_fb_redirect, detect_creative_format, extract_cta


class TestScraperModules(unittest.TestCase):
    def test_settings_directories(self):
        self.assertTrue(BASE_DIR.exists())
        self.assertTrue(DATA_DIR.exists())
        self.assertTrue(RAW_DATA_DIR.exists())
        self.assertTrue(PROCESSED_DATA_DIR.exists())
        self.assertTrue(CREATIVES_DIR.exists())  # data/creatives (verified assets root)
        self.assertEqual(len(TARGET_BRANDS), 5)

    def test_decode_fb_redirect(self):
        encoded = "https://l.facebook.com/l.php?u=https%3A%2F%2Fkapiva.in%2Fdia-free-juice%2F"
        decoded = decode_fb_redirect(encoded)
        self.assertEqual(decoded, "https://kapiva.in/dia-free-juice/")

        direct = "https://kapiva.in/products"
        self.assertEqual(decode_fb_redirect(direct), direct)
        self.assertIsNone(decode_fb_redirect(None))

    def test_extract_cta(self):
        self.assertEqual(extract_cta("KAPIVA.IN Shop now"), "Shop now")
        self.assertEqual(extract_cta("LINK.BLINKIT.COM Order Now"), "Order Now")
        self.assertEqual(extract_cta("MAMAEARTH.IN Learn More"), "Learn More")
        self.assertIsNone(extract_cta(None))

    def test_detect_creative_format(self):
        self.assertEqual(detect_creative_format(has_video=True), "Video")
        self.assertEqual(detect_creative_format(has_video=False), "Image")
        self.assertEqual(detect_creative_format(has_video=False, has_carousel=True), "Carousel")

    def test_build_search_url(self):
        url = build_search_url("Kapiva")
        self.assertIn("q=Kapiva", url)
        self.assertIn("country=IN", url)
        self.assertIn("active_status=all", url)


if __name__ == "__main__":
    unittest.main()


"""
AdVision AI — Configuration Settings
Central configuration module for Meta Ads Intelligence & Visual Clustering.
Uses pathlib for cross-platform file path resolution across macOS, Linux, and Windows.
"""

import os
from pathlib import Path

# Base directory (repository root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Core Data Directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"

# Creative Media Directory
CREATIVES_DIR = DATA_DIR / "creatives"                  # verified/<brand>/<ad_id>.<ext>
VERIFIED_CREATIVES_DIR = CREATIVES_DIR / "verified"
LEGACY_DIR = DATA_DIR / "legacy"                         # superseded dataset + creatives (audit only)
LEGACY_CREATIVES_DIR = LEGACY_DIR / "creatives"
LEGACY_DATASET_CSV = LEGACY_DIR / "all_brands_ads.csv"

# Documentation & Reports Directory
REPORTS_DIR = BASE_DIR / "reports"

# Project Metadata
PROJECT_NAME = "AdVision AI — Meta Ads Intelligence"
PROJECT_VERSION = "0.2.0"
DEFAULT_COUNTRY = "India"
DEFAULT_COUNTRY_CODE = "IN"
DEFAULT_AD_TYPE = "all"
DEFAULT_ACTIVE_STATUS = "all"

# Target Brands Configuration
TARGET_BRANDS = {
    "Kapiva": {
        "slug": "kapiva",
        "search_term": "Kapiva",
        "category": "Ayurvedic Health & Wellness",
        "primary_domain": "kapiva.in",
        "target_sample_size": 10,
    },
    "OZiva": {
        "slug": "oziva",
        "search_term": "OZiva",
        "category": "Plant-Based Nutrition & Clean Wellness",
        "primary_domain": "oziva.in",
        "target_sample_size": 10,
    },
    "Mamaearth": {
        "slug": "mamaearth",
        "search_term": "Mamaearth",
        "category": "Toxin-Free Personal Care & Beauty",
        "primary_domain": "mamaearth.in",
        "target_sample_size": 10,
    },
    "Himalaya Wellness": {
        "slug": "himalaya",
        "search_term": "Himalaya Wellness",
        "category": "Herbal Healthcare & Personal Care",
        "primary_domain": "himalayawellness.in",
        "target_sample_size": 10,
    },
    "MuscleBlaze": {
        "slug": "muscleblaze",
        "search_term": "MuscleBlaze",
        "category": "Sports Nutrition & Fitness Supplements",
        "primary_domain": "muscleblaze.com",
        "target_sample_size": 10,
    },
}

# Slugs mapping for backward compatibility and directory resolution
BRAND_SLUG_MAP = {
    "Kapiva": "kapiva",
    "OZiva": "oziva",
    "Mamaearth": "mamaearth",
    "Himalaya Wellness": "himalaya",
    "MuscleBlaze": "muscleblaze",
}

# Meta Ad Library URLs
META_AD_LIBRARY_BASE_URL = "https://www.facebook.com/ads/library/"
META_AD_DETAIL_URL_TEMPLATE = "https://www.facebook.com/ads/library/?id={ad_id}"

# Playwright & Browser Automation Settings
BROWSER_CONFIG = {
    "headless": True,
    "viewport": {"width": 1280, "height": 800},
    "timeout_ms": 30000,
    "page_settle_delay_ms": 2500,
    "user_agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

# Expected Dataset Files
DATASET_FILES = {
    "legacy_json": DATA_DIR / "legacy" / "all_brands_ads.json",
    "legacy_csv": DATA_DIR / "legacy" / "all_brands_ads.csv",
    "validated_csv": PROCESSED_DATA_DIR / "validated_dataset.csv",
    "validated_json": PROCESSED_DATA_DIR / "validated_dataset.json",
    "raw_brands": {
        brand: RAW_DATA_DIR / f"{meta['slug']}_ads.json"
        for brand, meta in TARGET_BRANDS.items()
    },
}


# Visual Feature Extraction Settings (src/vision). Each value can be overridden by
# the environment variable named in the comment, or by feature_pipeline CLI flags.
VISION_CONFIG = {
    # Longest side (px) of the downscaled copy used for colour/brightness statistics.
    "analysis_max_side": int(os.getenv("ADVISION_ANALYSIS_MAX_SIDE", "512")),
    # Short side (px) that sharpness is normalised to, so scores compare across sizes.
    "sharpness_short_side": 600,
    # Number of k-means clusters for dominant colour extraction.
    "n_dominant_colours": 5,
    # open_clip model + pretrained tag (weights are downloaded once into the HF cache).
    "clip_model": os.getenv("ADVISION_CLIP_MODEL", "ViT-B-32"),
    "clip_pretrained": os.getenv("ADVISION_CLIP_PRETRAINED", "laion2b_s34b_b79k"),
    # "cpu" (default, bit-reproducible), "mps" (Apple GPU), "cuda", or "auto".
    "clip_device": os.getenv("ADVISION_CLIP_DEVICE", "cpu"),
    "clip_batch_size": int(os.getenv("ADVISION_CLIP_BATCH_SIZE", "16")),
    # OCR: recognitions below this confidence are excluded from ocr_text
    # (their boxes still count towards text_density, since detection is script-agnostic).
    "ocr_min_confidence": 0.5,
    "visual_features_json": PROCESSED_DATA_DIR / "visual_features.json",
    "clip_embeddings_npy": PROCESSED_DATA_DIR / "clip_embeddings.npy",
}

# Official advertiser pages per canonical brand, as observed on live Ad Library cards
# (advertiser name -> Facebook page handle/ID from the card's page link). An advertiser is
# accepted only if it is listed here, or is a partnership ad "<creator> with <listed name>".
# Look-alike names (e.g. "Himalayan Organics") are NOT accepted automatically: they get
# advertiser_verification_status = NEEDS_REVIEW. Evidence: data/quality/live_cards.json,
# data/quality/replacement_cards.json, reports/himalaya_brand_consolidation.md.
OFFICIAL_ADVERTISERS = {
    "Kapiva": {
        "Kapiva": "kapiva.official",
        "Kapiva Performance": "100089581512473",
        "Daily Wellness Solutions by Kapiva": "kapivadailywellness",
        "Chronic Health Solutions by Kapiva": "kapivahealth",
        "Kapiva Wellness": "kapivaskincare",
    },
    "OZiva": {"OZiva": "OzivaLife"},
    "Mamaearth": {"Mamaearth": "Mamaearthindia"},
    "Himalaya Wellness": {
        "Himalaya Hair Care": "HimalayaHairCare",
        "Himalaya Personal Care": "HimalayaPersonalCare",
    },
    "MuscleBlaze": {"MuscleBlaze": "MuscleBlaze"},
}

# Raw brand labels / folder names seen in legacy data -> canonical brand name.
BRAND_ALIASES = {
    "Himalaya": "Himalaya Wellness",
    "Himalaya Wellness": "Himalaya Wellness",
    "himalaya": "Himalaya Wellness",
    "himalaya_wellness": "Himalaya Wellness",
    "Kapiva": "Kapiva", "OZiva": "OZiva", "Mamaearth": "Mamaearth", "MuscleBlaze": "MuscleBlaze",
}

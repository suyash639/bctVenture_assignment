"""
AdVision AI — Data Cleaning & Consolidation Preprocessor
Reads raw ad datasets, normalizes fields, links verified local creative image paths,
and exports consolidated master datasets (CSV and JSON).
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from config.settings import (
    BASE_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    CREATIVES_DIR,
    TARGET_BRANDS,
    BRAND_SLUG_MAP,
    PROJECT_NAME,
    DEFAULT_COUNTRY,
)
from src.utils.image_validator import inspect_png_header

# Canonical field order for CSV and JSON export
CANONICAL_FIELDS = [
    "brand",
    "brand_name",
    "ad_id",
    "ad_library_id",
    "page_name",
    "ad_library_url",
    "status",
    "start_date",
    "end_date",
    "ad_copy",
    "link_headline",
    "cta",
    "creative_format",
    "has_multiple_versions",
    "landing_page_url",
    "landing_url_fb_redirect",
    "creative_image_url",
    "collection_date",
    "country",
    "data_source",
    "local_image_path",
    "image_download_status",
    "creative_capture_method",
    "image_quality_status",
    "image_type",
    "image_dimensions",
    "image_size_kb",
    "replacement_status",
    "replacement_reason",
    "original_ad_id",
    "original_creative_format",
    "original_image_path",
]


def load_raw_brand_datasets() -> Dict[str, List[Dict[str, Any]]]:
    """Load all brand raw JSON files from data/raw/."""
    brand_ads: Dict[str, List[Dict[str, Any]]] = {}
    
    for brand_name, meta in TARGET_BRANDS.items():
        slug = meta["slug"]
        raw_file = RAW_DATA_DIR / f"{slug}_ads.json"
        
        if not raw_file.exists():
            raise FileNotFoundError(f"Raw dataset missing for brand '{brand_name}': {raw_file}")
            
        with open(raw_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        ads = data.get("ads", []) if isinstance(data, dict) else data
        brand_ads[brand_name] = ads

    return brand_ads


def normalize_ad_record(ad: Dict[str, Any], brand_name: str) -> Dict[str, Any]:
    """Ensure consistent schema, normalize paths, and link local creative images."""
    normalized = dict(ad)
    normalized["brand"] = brand_name
    normalized["brand_name"] = brand_name

    ad_id = str(normalized.get("ad_library_id", normalized.get("ad_id", ""))).strip()
    normalized["ad_id"] = ad_id
    normalized["ad_library_id"] = ad_id
    
    # Ensure all canonical fields are present with None default
    for field in CANONICAL_FIELDS:
        if field not in normalized:
            normalized[field] = None

    slug = BRAND_SLUG_MAP.get(brand_name, brand_name.lower().replace(" ", "_"))
    
    # Canonical creative path
    rel_image_path = f"creatives/{slug}/{ad_id}.png"
    full_image_path = BASE_DIR / rel_image_path
    
    # Fallback check for himalaya_wellness alias
    if not full_image_path.exists() and slug == "himalaya":
        alt_path = BASE_DIR / f"creatives/himalaya_wellness/{ad_id}.png"
        if alt_path.exists():
            full_image_path = alt_path

    if full_image_path.exists():
        is_valid, size, w, h = inspect_png_header(full_image_path)
        if is_valid and size > 1000:
            format_type = normalized.get("creative_format", "Image")
            normalized["local_image_path"] = rel_image_path
            normalized["image_download_status"] = "success"
            normalized["creative_capture_method"] = (
                normalized.get("creative_capture_method") or "browser_element_unconstrained_screenshot"
            )
            normalized["image_dimensions"] = f"{w}x{h}" if (w and h) else None
            normalized["image_size_kb"] = round(size / 1024.0, 1) if size else 0.0
            
            # Evaluate quality status (prefer >= 600px shorter side)
            min_dim = min(w or 0, h or 0)
            if min_dim >= 600:
                normalized["image_quality_status"] = "PASS"
                normalized["image_type"] = "static"
            elif format_type == "Video":
                normalized["image_quality_status"] = "VIDEO_ONLY"
                normalized["image_type"] = "video_thumbnail"
            else:
                normalized["image_quality_status"] = "REPLACE"
                normalized["image_type"] = "static"
        else:
            normalized["local_image_path"] = rel_image_path
            normalized["image_download_status"] = "failed_corrupt_file"
            normalized["creative_capture_method"] = None
            normalized["image_quality_status"] = "REPLACE"
    else:
        normalized["local_image_path"] = None
        normalized["image_download_status"] = "missing_file"
        normalized["creative_capture_method"] = None
        normalized["image_quality_status"] = "REPLACE"

    return normalized


def consolidate_datasets(output_csv: Optional[Path] = None, output_json: Optional[Path] = None) -> Dict[str, Any]:
    """
    Consolidates raw brand files into master CSV and JSON datasets.

    Args:
        output_csv: Path to save all_brands_ads.csv (defaults to PROCESSED_DATA_DIR / all_brands_ads.csv)
        output_json: Path to save all_brands_ads.json (defaults to PROCESSED_DATA_DIR / all_brands_ads.json)

    Returns:
        Summary dictionary of the consolidation process.
    """
    csv_path = output_csv or (PROCESSED_DATA_DIR / "all_brands_ads.csv")
    json_path = output_json or (PROCESSED_DATA_DIR / "all_brands_ads.json")

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    raw_brands = load_raw_brand_datasets()
    all_normalized_ads: List[Dict[str, Any]] = []
    brand_counts: Dict[str, int] = {}
    brand_image_success: Dict[str, int] = {}

    for brand_name, ads in raw_brands.items():
        normalized_brand_ads = []
        success_images = 0
        for ad in ads:
            norm_ad = normalize_ad_record(ad, brand_name)
            normalized_brand_ads.append(norm_ad)
            all_normalized_ads.append(norm_ad)
            if norm_ad.get("image_download_status") == "success":
                success_images += 1

        brand_counts[brand_name] = len(normalized_brand_ads)
        brand_image_success[brand_name] = success_images

        # Update the raw brand file to keep it in sync
        raw_file = RAW_DATA_DIR / f"{BRAND_SLUG_MAP[brand_name]}_ads.json"
        with open(raw_file, "r", encoding="utf-8") as f:
            raw_content = json.load(f)
        raw_content["ads"] = normalized_brand_ads
        if "meta" in raw_content:
            raw_content["meta"]["image_acquisition_completed"] = (success_images == len(normalized_brand_ads))
            raw_content["meta"]["total_creatives_acquired"] = success_images
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(raw_content, f, indent=2, ensure_ascii=False)

    # 1. Write Consolidated Master JSON
    total_images = sum(brand_image_success.values())
    master_json_content = {
        "meta": {
            "project": PROJECT_NAME,
            "description": "Meta Ad Library Collection across 5 Indian wellness, D2C & fitness brands",
            "country": DEFAULT_COUNTRY,
            "ad_category": "All Ads",
            "collection_date": "2026-11-13",
            "total_brands": len(brand_counts),
            "total_records": len(all_normalized_ads),
            "records_per_brand": brand_counts,
            "access_method": "Playwright headless browser (public, no login, permitted access)",
            "image_acquisition_completed": (total_images == len(all_normalized_ads)),
            "total_creatives_acquired": total_images,
            "creative_acquisition_success_rate": f"{(total_images / len(all_normalized_ads) * 100):.1f}%",
        },
        "ads": all_normalized_ads,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(master_json_content, f, indent=2, ensure_ascii=False)

    # 2. Write Consolidated Master CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        for ad in all_normalized_ads:
            row = {k: ad.get(k, "") for k in CANONICAL_FIELDS}
            writer.writerow(row)

    return {
        "total_records": len(all_normalized_ads),
        "total_brands": len(brand_counts),
        "brand_counts": brand_counts,
        "total_creatives_acquired": total_images,
        "csv_path": str(csv_path),
        "json_path": str(json_path),
    }


if __name__ == "__main__":
    result = consolidate_datasets()
    print(f"[✓] Successfully consolidated {result['total_records']} ads across {result['total_brands']} brands.")
    print(f"[✓] Master JSON: {result['json_path']}")
    print(f"[✓] Master CSV:  {result['csv_path']}")
    print(f"[✓] Total creatives linked: {result['total_creatives_acquired']}/{result['total_records']}")


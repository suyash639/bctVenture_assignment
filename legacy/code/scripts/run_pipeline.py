#!/usr/bin/env python3
"""
AdVision AI — Unified Pipeline CLI Runner
Entry point for running validation, data preprocessing, and dataset status inspection.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import CREATIVES_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR, TARGET_BRANDS
from src.preprocessing.clean_data import consolidate_datasets
from src.utils.image_validator import validate_creative_images


def print_banner():
    print("=" * 70)
    print("  AdVision AI — Meta Ads Intelligence & Creative Analysis Pipeline")
    print("=" * 70)


def run_validation():
    print("\n[1/2] Validating Creative Images on Disk...")
    results = validate_creative_images(CREATIVES_DIR)
    
    print(f"Total Images Found: {results['total_files']}")
    print(f"Valid PNG Images:   {results['total_valid']} ({results['success_rate']})")
    print(f"Corrupt / Missing:  {results['total_corrupt']}")
    print("-" * 70)
    print(f"{'Brand Directory':<20} | {'Count':<6} | {'Avg Size (KB)':<14} | {'Status'}")
    print("-" * 70)
    for brand, stats in results["brands"].items():
        status_str = "✓ VALID" if stats["is_all_valid"] else "✗ ISSUES"
        print(f"{brand:<20} | {stats['total_files']:<6} | {stats['avg_size_kb']:<14.1f} | {status_str}")
    print("-" * 70)
    return results["total_corrupt"] == 0


def run_cleaning():
    print("\n[2/2] Consolidating Datasets into Master CSV and JSON...")
    summary = consolidate_datasets()
    print(f"✓ Consolidated {summary['total_records']} ad records across {summary['total_brands']} brands.")
    print(f"✓ Master JSON: {summary['json_path']}")
    print(f"✓ Master CSV:  {summary['csv_path']}")
    print(f"✓ Creatives Successfully Linked: {summary['total_creatives_acquired']}/{summary['total_records']}")
    return True


def run_status_summary():
    print("\n--- Project Data Status Summary ---")
    master_json = PROCESSED_DATA_DIR / "all_brands_ads.json"
    if not master_json.exists():
        print(f"Master dataset not found at {master_json}. Please run with --clean first.")
        return

    with open(master_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    ads = data.get("ads", [])

    print(f"Project:         {meta.get('project', 'AdVision AI')}")
    print(f"Total Brands:    {meta.get('total_brands', len(TARGET_BRANDS))}")
    print(f"Total Ads:       {len(ads)}")
    print(f"Image Coverage:  {meta.get('creative_acquisition_success_rate', 'N/A')}")
    print("\nRecords per Brand:")
    for brand, count in meta.get("records_per_brand", {}).items():
        print(f"  - {brand}: {count} ads")


def main():
    parser = argparse.ArgumentParser(description="AdVision AI Pipeline Runner")
    parser.add_argument("--validate", action="store_true", help="Validate creative image integrity")
    parser.add_argument("--clean", action="store_true", help="Run data cleaning and generate consolidated datasets")
    parser.add_argument("--summary", action="store_true", help="Print dataset coverage and status summary")
    parser.add_argument("--all", action="store_true", help="Run validation, cleaning, and summary in sequence")

    args = parser.parse_args()

    print_banner()

    if not any([args.validate, args.clean, args.summary, args.all]):
        # Default behavior: run all
        args.all = True

    if args.all or args.validate:
        run_validation()

    if args.all or args.clean:
        run_cleaning()

    if args.all or args.summary:
        run_status_summary()

    print("\n[✓] Pipeline execution finished successfully.\n")


if __name__ == "__main__":
    main()


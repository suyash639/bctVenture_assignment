"""
CLI: verify Ad Library IDs against their live single-ad cards and recover each card's own creative.

  python scripts/verify_creatives.py verify [--out F] [--workers N] [--refresh] [--staging-dir D] [--delay-ms MS] [ad_id ...]
  python scripts/verify_creatives.py page <page_id> [--media image|all] [--status active|all] [--scrolls N]

With no IDs, verifies every ID in the legacy dataset (data/legacy/all_brands_ads.csv).
Library code and the per-ad data contract: src/scraper/ad_library_cards.py.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scraper.ad_library_cards import (  # noqa: E402,F401
    BASE,
    CARD_JS,
    DEFAULT_OUT,
    STAGING,
    fetch_card,
    list_page,
    load_json,
    parse_card,
    save_json,
    verify,
)


def dataset_ids() -> list:
    with open(ROOT / "data/legacy/all_brands_ads.csv") as f:
        return [r["ad_id"] for r in csv.DictReader(f)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify")
    v.add_argument("ids", nargs="*")
    v.add_argument("--out", type=Path, default=DEFAULT_OUT)
    v.add_argument("--workers", type=int, default=2)
    v.add_argument("--refresh", action="store_true")
    v.add_argument("--staging-dir", type=Path, default=None,
                   help="where downloaded assets go (default data/quality/staging); use a fresh dir to keep earlier evidence")
    v.add_argument("--delay-ms", type=int, default=0, help="extra polite pause between pages per worker")
    pg = sub.add_parser("page")
    pg.add_argument("page_id")
    pg.add_argument("--media", default="image")
    pg.add_argument("--status", default="active")
    pg.add_argument("--scrolls", type=int, default=4)
    a = ap.parse_args()
    if a.cmd == "verify":
        out = a.out if a.out.is_absolute() else ROOT / a.out
        stg = None if a.staging_dir is None else (a.staging_dir if a.staging_dir.is_absolute() else ROOT / a.staging_dir)
        asyncio.run(verify(a.ids or dataset_ids(), out, a.workers, a.refresh, stg, a.delay_ms))
    else:
        ids = asyncio.run(list_page(a.page_id, a.media, a.status, a.scrolls))
        print(json.dumps(ids))

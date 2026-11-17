"""
Freeze the validated dataset: write data/processed/DATASET_FROZEN.json with its sha256.

    python -m src.pipeline.freeze [--dataset data/processed/validated_dataset.csv] [--note "..."]

Refuses unless data/quality/dataset_integrity_report.json passed and every VERIFIED row
satisfies all five acceptance statuses. Any later edit to the dataset changes its hash, and
`src.pipeline.run` then refuses a final run until the dataset is re-frozen.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ACCEPT = {"advertiser_verification_status": {"VERIFIED"}, "image_verification_status": {"VERIFIED"},
          "metadata_verification_status": {"VERIFIED"}, "image_quality_status": {"PASS"},
          "duplicate_status": {"UNIQUE", "GROUP_REPRESENTATIVE", "NEAR_DUPLICATE_KEPT"}}


def check(dataset: Path, integrity: Path) -> list:
    problems = []
    if not integrity.is_file():
        problems.append(f"integrity report missing: {integrity}")
    elif not json.loads(integrity.read_text()).get("passed"):
        problems.append("integrity report did not pass")
    rows = list(csv.DictReader(open(dataset, encoding="utf-8")))
    ver = [r for r in rows if r.get("final_status") == "VERIFIED"]
    if not ver:
        problems.append("no VERIFIED rows")
    from config.settings import OFFICIAL_ADVERTISERS, TARGET_BRANDS
    seen_paths, seen_sha = {}, {}
    for r in ver:
        bad = [k for k, ok in ACCEPT.items() if r.get(k) not in ok]
        if bad:
            problems.append(f"{r['ad_id']}: VERIFIED but {bad}")
        if r.get("brand") not in TARGET_BRANDS:
            problems.append(f"{r['ad_id']}: non-canonical brand {r.get('brand')!r}")
            continue
        official = OFFICIAL_ADVERTISERS.get(r["brand"], {})
        adv = r.get("advertiser") or ""
        if not (adv in official or (" with " in adv and adv.rsplit(" with ", 1)[1] in official)):
            problems.append(f"{r['ad_id']}: advertiser {adv!r} is not an allowlisted official page of {r['brand']}")
        img = ROOT / (r.get("local_image_path") or "-")
        if not img.is_file():
            problems.append(f"{r['ad_id']}: image file missing")
        elif hashlib.sha256(img.read_bytes()).hexdigest() != r.get("image_sha256"):
            problems.append(f"{r['ad_id']}: image sha256 does not match the file on disk")
        for key, seen in (("local_image_path", seen_paths), ("image_sha256", seen_sha)):
            if r.get(key) in seen:
                problems.append(f"{r['ad_id']}: {key} shared with {seen[r.get(key)]}")
            seen[r.get(key)] = r["ad_id"]
    ids = [r["ad_id"] for r in rows]
    if len(ids) != len(set(ids)):
        problems.append("duplicate ad_id rows")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, default=ROOT / "data/processed/validated_dataset.csv")
    ap.add_argument("--integrity", type=Path, default=ROOT / "data/quality/dataset_integrity_report.json")
    ap.add_argument("--marker", type=Path, default=ROOT / "data/processed/DATASET_FROZEN.json")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    problems = check(a.dataset, a.integrity)
    if problems:
        print("REFUSING TO FREEZE:\n  " + "\n  ".join(problems))
        return 1
    rows = list(csv.DictReader(open(a.dataset, encoding="utf-8")))
    ver = [r for r in rows if r["final_status"] == "VERIFIED"]
    marker = {"dataset": str(a.dataset.resolve().relative_to(ROOT)),
              "dataset_sha256": hashlib.sha256(a.dataset.read_bytes()).hexdigest(),
              "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "n_verified": len(ver),
              "verified_per_brand": {b: sum(1 for r in ver if r["brand"] == b) for b in sorted({r["brand"] for r in ver})},
              "note": a.note}
    a.marker.write_text(json.dumps(marker, indent=1))
    print(json.dumps(marker, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

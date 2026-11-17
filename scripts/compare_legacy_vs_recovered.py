"""Side-by-side sheet: legacy capture (left) vs asset recovered from the exact live card (right).
Usage: python scripts/compare_legacy_vs_recovered.py <brand_slug> <out.png> [cards.json]"""
import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
slug, out = sys.argv[1], Path(sys.argv[2])
cards = json.loads((ROOT / (sys.argv[3] if len(sys.argv) > 3 else "data/quality/live_cards.json")).read_text())
rows = [r for r in csv.DictReader(open(ROOT / "data/legacy/all_brands_ads.csv"))
        if r["local_image_path"].split("/")[1] == slug]
T, H = 260, 22
sheet = Image.new("RGB", (2 * T + 30, len(rows) * (T + H)), "white")
d = ImageDraw.Draw(sheet)
for i, r in enumerate(rows):
    y = i * (T + H)
    c = cards.get(r["ad_id"], {})
    for j, p in enumerate([ROOT / "data/legacy" / r["local_image_path"], ROOT / c.get("asset_path", "-")]):
        if p.is_file():
            im = Image.open(p).convert("RGB")
            w, h = im.size
            im.thumbnail((T, T))
            sheet.paste(im, (j * (T + 30) + (T - im.width) // 2, y + H))
            d.text((j * (T + 30) + 2, y + 4), f"{'legacy' if j == 0 else 'recovered'} {r['ad_id']} {w}x{h}"
                   + ("" if j == 0 else f" {c.get('advertiser', '')[:18]}"), fill="black")
sheet.save(out)
print(out, len(rows))

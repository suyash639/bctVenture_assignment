"""
Cluster contact sheets: one PNG per cluster (plus "noise" and "unassigned" when present).
Every member gets a tile labelled "<brand> · <ad_id>"; representatives are outlined. An image
that cannot be loaded still gets a tile with "IMAGE MISSING" text and is listed with its reason,
so it is never silently dropped. Original image files are only read.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set

from PIL import Image, ImageDraw, ImageFont

from src.analytics.common import AnalyticsInput, Manifest, cluster_label, image_path_of, write_csv

TILE = 220
LABEL_H = 34
COLS = 5
PAD = 8


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def _load_tile(path: Optional[Path]):
    from src.vision.preprocessing import ImageLoadError, load_image
    if path is None:
        return None, "no image path in record"
    try:
        im = load_image(path).rgb.copy()
    except ImageLoadError as e:
        return None, f"image unreadable: {e}"
    im.thumbnail((TILE, TILE))
    return im, None


def render_sheet(title: str, ad_ids: List[str], inp: AnalyticsInput, base_dir, out_path: Path,
                 highlight: Set[str] = frozenset()):
    """Returns (tile_rows, missing). tile_rows map each tile position -> ad_id."""
    n = max(1, len(ad_ids))
    cols = min(COLS, n)
    rows = (n + cols - 1) // cols
    W = cols * (TILE + PAD) + PAD
    H = 40 + rows * (TILE + LABEL_H + PAD) + PAD
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 10), title, fill="black", font=_font(18))
    tiles, missing = [], []
    for i, ad in enumerate(ad_ids):
        r, c = divmod(i, cols)
        x, y = PAD + c * (TILE + PAD), 40 + r * (TILE + LABEL_H + PAD)
        im, err = _load_tile(image_path_of(inp.records.get(ad, {}), base_dir))
        if im is None:
            d.rectangle([x, y, x + TILE, y + TILE], fill="#F2F2F2", outline="#B00020", width=2)
            d.text((x + 10, y + TILE // 2 - 8), "IMAGE MISSING", fill="#B00020", font=_font(14))
            missing.append({"ad_id": ad, "reason": err})
        else:
            sheet.paste(im, (x + (TILE - im.width) // 2, y + (TILE - im.height) // 2))
        if ad in highlight:
            d.rectangle([x - 3, y - 3, x + TILE + 3, y + TILE + 3], outline="#0072B2", width=3)
        d.text((x, y + TILE + 3), f"{inp.brands[ad]}", fill="black", font=_font(12))
        d.text((x, y + TILE + 18), f"{ad}" + ("  [rep]" if ad in highlight else ""), fill="#333333", font=_font(11))
        tiles.append({"tile_index": i, "row": r, "col": c, "ad_id": ad, "brand": inp.brands[ad],
                      "representative": ad in highlight, "image_loaded": im is not None})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return tiles, missing


def cluster_contact_sheets(inp: AnalyticsInput, out_dir: Path, manifest: Manifest, base_dir=".",
                           representatives: Optional[Dict[str, dict]] = None) -> List[dict]:
    out_dir = Path(out_dir) / "contact_sheets"
    reps = {r["ad_id"] for v in (representatives or {}).values() for r in v["representatives"]}
    entries = []
    for c in inp.ordered_clusters:
        lab = cluster_label(c)
        members = sorted(inp.members(c), key=lambda a: (inp.brands[a], a))
        png = out_dir / f"cluster_{lab}.png"
        tiles, missing_img = render_sheet(f"{lab}  ({len(members)} ads)", members, inp, base_dir, png,
                                          highlight=reps & set(members))
        mp = write_csv(out_dir / f"cluster_{lab}.csv", tiles)
        others = [{"ad_id": a, "reason": f"belongs to {cluster_label(inp.clusters[a])}, shown on that sheet"}
                  for a in inp.ad_ids if a not in members]
        # an ad whose image failed is still on this sheet as a placeholder tile: covered, with a note
        entries.append(manifest.add(png, "contact_sheet", f"All members of {lab}; tiles labelled brand + ad_id; "
                                    "representatives outlined in blue", covered=members, missing=others,
                                    mapping=mp, extra={"cluster": lab, "image_load_failures": missing_img}))
    return entries

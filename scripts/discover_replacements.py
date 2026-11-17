"""
AdVision AI — same-brand replacement discovery (workstream 3).

1. `list`: load an advertiser's own public Ad Library listing (view_all_page_id) with a
   media filter and read the ads embedded in the page (ad_archive_id, page_id, page_name,
   display_format, collation_count). Results accumulate in
   data/quality/replacement_listing.json (scratch, owned by this workstream).
2. `verify`: verify chosen IDs against their exact single-ad cards via
   scripts/verify_creatives.verify -> data/quality/replacement_cards.json.

Public pages only; no login / CAPTCHA / rate-limit bypass. Stops on a login wall.

Usage:
  python scripts/discover_replacements.py list <page_id> [--media image] [--status active] [--scrolls 4]
  python scripts/discover_replacements.py verify <ad_id> ...
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from verify_creatives import fetch_card, load_json, save_json, verify  # noqa: E402

from src.scraper.browser import launch_browser  # noqa: E402

CONTROL_ID = "1575470834177468"  # known-good Mamaearth ad; used to detect soft throttling

LISTING = ROOT / "data/quality/replacement_listing.json"
CARDS = ROOT / "data/quality/replacement_cards.json"


CARDS_JS = r"""() => {
  const leaves = [...document.querySelectorAll('div,span')].filter(
    e => e.children.length === 0 && /^Library ID: \d+$/.test(e.textContent.trim()));
  return leaves.map(leaf => {
    let card = leaf, c = leaf;
    while (c && c !== document.body) {
      const n = (c.innerText.match(/Library ID:/g) || []).length;
      if (n === 1) card = c; else if (n > 1) break;
      c = c.parentElement;
    }
    const t = card.innerText;
    const m = t.match(/See (?:ad|summary) details\n+([^\n]+)/);
    const s = t.match(/(\d+) ads use this creative/);
    return {id: leaf.textContent.trim().replace('Library ID: ', ''), adv: m ? m[1].trim() : null,
            video: !!card.querySelector('video'),
            imgs: [...card.querySelectorAll('img')].filter(i => i.naturalWidth >= 200).length,
            same: s ? +s[1] : 1};
  });
}"""


def parse_embedded(html: str) -> dict:
    out = {}
    for m in re.finditer(r'"ad_archive_id":"(\d+)"', html):
        seg = html[m.start(): m.start() + 8000]
        nxt = seg.find('"ad_archive_id"', 20)
        if nxt > 0:
            seg = seg[:nxt]
        g = lambda k: (re.search(rf'"{k}":"?([^",}}]*)"?', seg) or [None, None])[1]  # noqa: E731
        out[m.group(1)] = {"page_id": g("page_id"), "page_name": g("page_name"),
                           "display_format": g("display_format"), "collation_count": g("collation_count"),
                           "is_active": g("is_active")}
    return out


async def list_page(page_id: str, media: str, status: str, scrolls: int) -> dict:
    url = (f"https://www.facebook.com/ads/library/?active_status={status}&ad_type=all&country=IN"
           f"&media_type={media}&view_all_page_id={page_id}&locale=en_GB")
    async with launch_browser(headless=True) as page:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        for _ in range(scrolls):
            await page.mouse.wheel(0, 6000)
            await page.wait_for_timeout(2500)
        text = await page.evaluate("() => document.body.innerText")
        if "No ads match" in text:
            print("listing: no ads match these filters")
        elif "Library ID" not in text and re.search(r"Log in to continue|You must log in|Log into Facebook", text, re.I):
            raise SystemExit("STOP: login wall on listing page; not bypassing")
        cards = await page.evaluate(CARDS_JS)
    # format is a pre-filter only; every chosen ID is re-verified on its own single-ad page
    return {c["id"]: {"page_id": page_id, "listing_advertiser": c["adv"], "has_video": c["video"],
                      "n_images": c["imgs"], "same_creative": c["same"], "visible_in_listing": True}
            for c in cards}


async def verify_slow(ids: list, delay: float) -> None:
    """Sequential, delayed verification. Stops (never retries harder) when Meta serves empty
    result pages: a control ID that previously verified is checked first and again after any
    empty page, so 'not found' is only recorded when the control still loads."""
    cards = load_json(CARDS)
    todo = [i for i in ids if not cards.get(i, {}).get("asset_sha256")]
    async with launch_browser(headless=True) as page:
        ctl = await fetch_card(page, CONTROL_ID)
        if not ctl.get("found"):
            print("THROTTLED: control ad not served; stopping without retrying", flush=True)
            return
        for i in todo:
            await asyncio.sleep(delay)
            r = await fetch_card(page, i)
            if not r.get("found"):
                await asyncio.sleep(delay)
                ctl = await fetch_card(page, CONTROL_ID)
                if not ctl.get("found"):
                    print(f"THROTTLED at {i}: control ad not served; stopping", flush=True)
                    return
                r["not_found_with_control_ok"] = True
            cards[i] = r
            save_json(CARDS, cards)
            print(i, r.get("found"), r.get("advertiser"), r.get("format"), r.get("asset_width"), r.get("asset_height"), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("list")
    lp.add_argument("page_id")
    lp.add_argument("--media", default="image")
    lp.add_argument("--status", default="active")
    lp.add_argument("--scrolls", type=int, default=4)
    vp = sub.add_parser("verify")
    vp.add_argument("ids", nargs="+")
    vp.add_argument("--workers", type=int, default=2)
    vp.add_argument("--slow", type=float, default=None, help="sequential mode with this delay (s) between ads")
    a = ap.parse_args()
    if a.cmd == "list":
        res = asyncio.run(list_page(a.page_id, a.media, a.status, a.scrolls))
        allr = load_json(LISTING)
        key = f"{a.page_id}|{a.media}|{a.status}"
        allr[key] = res
        save_json(LISTING, allr)
        vis = [k for k, v in res.items() if v["visible_in_listing"]]
        print(f"{key}: {len(vis)} visible cards, {len(res)} total ids")
        for k in vis:
            print(k, res[k].get("listing_advertiser"), "VIDEO" if res[k].get("has_video") else f"img{res[k].get('n_images')}",
                  "same=", res[k].get("same_creative"))
    else:
        if a.slow is not None:
            asyncio.run(verify_slow(a.ids, a.slow))
        else:
            asyncio.run(verify(a.ids, CARDS, a.workers))

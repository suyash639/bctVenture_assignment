"""
AdVision AI — ground-truth Ad Library card verification & creative recovery.

For each ad ID, loads the public single-ad Ad Library page, isolates the card whose
"Library ID" equals that ad, and records what the live card actually shows: advertiser,
status, dates, body copy, link caption/headline, CTA, landing URL, format, and the
card's own creative asset (static <img> or <video> poster), downloaded exactly as
served (no page screenshot, no UI chrome, no neighbouring cards, no upscaling).

Also lists ads from an advertiser's own page (view_all_page_id) to source same-brand
replacements.

Data contract (one JSON object per ad, keyed by ad_id, written incrementally):
  found, advertiser, page_link, status, dates, start_date, end_date, body, link_caption,
  link_headline, cta, landing_url, landing_url_fb_redirect, n_ads_same_creative,
  multiple_versions, format (static|carousel|video), asset_kind (static|video_thumbnail),
  asset_url, asset_path, asset_sha256, asset_width, asset_height, asset_bytes,
  retrieval_method, retrieved_at, card_text, error

No login, CAPTCHA, rate-limit or access-control bypass is attempted: pages are loaded
politely (sequential per worker, multi-second settle), and a run stops if Meta serves a
login wall or block page.

CLI (scripts/verify_creatives.py):
  python scripts/verify_creatives.py verify [--out F] [--workers N] [--refresh] [ad_id ...]
  python scripts/verify_creatives.py page <page_id> [--media image|all] [--status active|all] [--scrolls N]
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]

from src.scraper.browser import launch_browser  # noqa: E402

QUALITY_DIR = ROOT / "data" / "quality"
STAGING = QUALITY_DIR / "staging"
DEFAULT_OUT = QUALITY_DIR / "live_cards.json"
BASE = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=IN&media_type=all&locale=en_GB"
CTA_WORDS = {"shop now", "learn more", "book now", "order now", "buy now", "sign up", "get offer",
             "install now", "download", "send message", "contact us", "subscribe", "watch more",
             "apply now", "get quote", "see menu", "call now", "send whatsapp message", "use app",
             "visit instagram profile", "save", "get directions", "listen now", "play game"}

CARD_JS = r"""(id) => {
  const leaf = [...document.querySelectorAll('div,span')].find(
    e => e.children.length === 0 && e.textContent.trim() === 'Library ID: ' + id);
  if (!leaf) {
    const t = document.body.innerText;
    return {found: false, login_wall: /Log in to continue|You must log in|Log into Facebook/i.test(t) && !/Library ID/.test(t),
            n_cards: (t.match(/Library ID:/g) || []).length};
  }
  let card = leaf, c = leaf;
  while (c && c !== document.body) {
    const n = (c.innerText.match(/Library ID:/g) || []).length;
    if (n === 1) card = c; else if (n > 1) break;
    c = c.parentElement;
  }
  const links = [...card.querySelectorAll('a[href]')].map(a => a.href);
  const imgs = [...card.querySelectorAll('img')]
    .filter(i => i.naturalWidth >= 200 || i.naturalHeight >= 200)
    .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}));
  const videos = [...card.querySelectorAll('video')]
    .map(v => ({poster: v.poster || null, w: v.videoWidth, h: v.videoHeight}));
  return {found: true, text: card.innerText, links, imgs, videos};
}"""

LIST_JS = r"""() => [...new Set([...document.body.innerText.matchAll(/Library ID: (\d+)/g)].map(m => m[1]))]"""


def _clean_lines(text: str) -> list:
    return [ln.strip() for ln in text.split("\n") if ln.strip() and ln.strip() not in ("​",)]


def parse_card(text: str, links: list) -> dict:
    lines = _clean_lines(text)
    lib_idx = next((i for i, ln in enumerate(lines) if ln.startswith("Library ID:")), len(lines))
    status = next((ln for ln in reversed(lines[:lib_idx]) if ln in ("Active", "Inactive")), None)
    out = {"status": status, "advertiser": None, "dates": None,
           "start_date": None, "end_date": None, "multiple_versions": "multiple versions" in text,
           "n_ads_same_creative": None, "body": None, "link_caption": None,
           "link_headline": None, "cta": None}
    m = re.search(r"(\d+) ads use this creative and text", text)
    out["n_ads_same_creative"] = int(m.group(1)) if m else 1
    for i, line in enumerate(lines):
        if line.startswith("Library ID:") and i + 1 < len(lines):
            out["dates"] = lines[i + 1]
            d = lines[i + 1]
            if d.startswith("Started running on "):
                out["start_date"] = d.replace("Started running on ", "")
            elif " - " in d:
                out["start_date"], out["end_date"] = [x.strip() for x in d.split(" - ", 1)]
        if line in ("See ad details", "See summary details") and i + 1 < len(lines):
            out["advertiser"] = lines[i + 1]
            rest = lines[i + 2:]
            if rest and rest[0] == "Sponsored":
                rest = rest[1:]
            # strip trailing video timer / duplicated carousel blocks for parsing
            rest = [r for r in rest if not re.fullmatch(r"\d+:\d+ / \d+:\d+", r)]
            cta_idx = next((j for j, r in enumerate(rest) if r.lower() in CTA_WORDS), None)
            if cta_idx is not None:
                out["cta"] = rest[cta_idx]
                pre = rest[:cta_idx]
                cap_idx = next((j for j, r in enumerate(pre)
                                if re.fullmatch(r"[A-Z0-9.\-/:_]+\.[A-Z]{2,}[A-Z0-9.\-/_?=&%]*", r)), None)
                if cap_idx is not None:
                    out["link_caption"] = pre[cap_idx]
                    out["link_headline"] = " ".join(pre[cap_idx + 1:]) or None
                    pre = pre[:cap_idx]
                out["body"] = "\n".join(pre) or None
            else:
                out["body"] = "\n".join(rest) or None
            break
    fb = next((h for h in links if "l.facebook.com/l.php" in h), None)
    out["landing_url_fb_redirect"] = fb
    out["landing_url"] = unquote(parse_qs(urlparse(fb).query).get("u", [None])[0]) if fb and "u=" in fb else None
    out["page_link"] = next((h for h in links if re.fullmatch(r"https://www\.facebook\.com/[^/?#]+/?", h)
                             and "/ads/" not in h), None)
    return out


def load_json(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}


def save_json(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1, ensure_ascii=False))
    tmp.replace(p)


async def fetch_card(page, ad_id: str, staging: Path = None) -> dict:
    await page.goto(f"{BASE}&id={ad_id}", wait_until="domcontentloaded")
    await page.wait_for_timeout(4500)
    info = await page.evaluate(CARD_JS, ad_id)
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if not info.get("found"):
        return {"ad_id": ad_id, "found": False, "login_wall": info.get("login_wall", False),
                "n_cards_on_page": info.get("n_cards"), "retrieved_at": now}
    rec = {"ad_id": ad_id, "found": True, **parse_card(info["text"], info["links"]),
           "card_text": info["text"][:3000], "retrieved_at": now}
    if info["imgs"]:
        rec.update(format="carousel" if len(info["imgs"]) > 1 else "static", asset_kind="static",
                   asset_url=info["imgs"][0]["src"], n_images=len(info["imgs"]),
                   retrieval_method="ad_library_card_img_src")
    elif info["videos"] and info["videos"][0]["poster"]:
        rec.update(format="video", asset_kind="video_thumbnail", asset_url=info["videos"][0]["poster"],
                   n_images=0, retrieval_method="ad_library_card_video_poster")
    else:
        rec.update(format="video" if info["videos"] else None, asset_kind=None, asset_url=None)
        return rec
    resp = await page.request.get(rec["asset_url"])
    if not resp.ok:
        rec["download_error"] = resp.status
        return rec
    body = await resp.body()
    from PIL import Image
    try:
        with Image.open(io.BytesIO(body)) as im:
            w, h, fmt = im.width, im.height, (im.format or "jpeg").lower()
    except Exception as e:
        rec["download_error"] = f"undecodable: {e}"
        return rec
    ext = {"jpeg": "jpg"}.get(fmt, fmt)
    staging = staging or STAGING
    staging.mkdir(parents=True, exist_ok=True)
    p = staging / f"{ad_id}.{ext}"
    p.write_bytes(body)
    rec.update(asset_path=str(p.relative_to(ROOT)), asset_sha256=hashlib.sha256(body).hexdigest(),
               asset_width=w, asset_height=h, asset_bytes=len(body))
    return rec


async def verify(ids: list, out: Path, workers: int = 2, refresh: bool = False,
                 staging: Path = None, delay_ms: int = 0) -> dict:
    live = load_json(out)
    todo = [i for i in dict.fromkeys(ids) if refresh or i not in live or not live[i].get("found")
            or "asset_sha256" not in live[i]]
    print(f"{len(ids)} ids, {len(todo)} to fetch, {workers} workers -> {out.relative_to(ROOT)}", flush=True)
    queue: asyncio.Queue = asyncio.Queue()
    for i in todo:
        queue.put_nowait(i)
    lock = asyncio.Lock()
    stop = asyncio.Event()
    walls = {"n": 0}

    async def worker(page, wid):
        while not queue.empty() and not stop.is_set():
            ad_id = queue.get_nowait()
            try:
                r = await fetch_card(page, ad_id, staging)
                if delay_ms:
                    await page.wait_for_timeout(delay_ms)
            except Exception as e:
                r = {"ad_id": ad_id, "found": False, "error": str(e)[:300],
                     "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            async with lock:
                live[ad_id] = r
                save_json(out, live)
                if r.get("login_wall"):
                    walls["n"] += 1
                    if walls["n"] >= 3:
                        print("STOP: login wall served 3 times; not attempting to bypass", flush=True)
                        stop.set()
                # Pages that render zero ad cards in a row = throttling. Back off, don't push.
                walls["empty"] = walls.get("empty", 0) + 1 if (not r.get("found") and r.get("n_cards_on_page") == 0) else 0
                if walls["empty"] >= 3:
                    print("STOP: 3 consecutive pages with 0 ad cards (rate limited); retry after a cool-down", flush=True)
                    stop.set()
            print(f"[w{wid}] {ad_id} found={r.get('found')} adv={r.get('advertiser')} "
                  f"fmt={r.get('format')} {r.get('asset_width')}x{r.get('asset_height')} "
                  f"{r.get('error') or r.get('download_error') or ''}", flush=True)

    async with launch_browser(headless=True) as page:
        pages = [page] + [await page.context.new_page() for _ in range(max(0, workers - 1))]
        await asyncio.gather(*(worker(p, k) for k, p in enumerate(pages)))
    return live


async def list_page(page_id: str, media: str = "image", status: str = "active", scrolls: int = 4) -> list:
    """Library IDs shown on an advertiser's own page listing (no verification)."""
    url = (f"https://www.facebook.com/ads/library/?active_status={status}&ad_type=all&country=IN"
           f"&media_type={media}&view_all_page_id={page_id}&locale=en_GB")
    async with launch_browser(headless=True) as page:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        for _ in range(scrolls):
            await page.mouse.wheel(0, 5000)
            await page.wait_for_timeout(2000)
        ids = await page.evaluate(LIST_JS)
    return ids

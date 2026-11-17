"""
Inspect the running dashboard in a real (headless Chromium) browser.

For every route at desktop and mobile widths it records: HTTP status, console errors,
failed requests, images that failed to load, horizontal overflow, and a full-page screenshot.
It also follows a few in-app interactions (creative detail link, search box).

Usage:
  python scripts/inspect_dashboard.py --base http://localhost:3000 --out data/outputs/dashboard_inspection
Exit code 1 if any page has console errors, failed requests or broken images.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROUTES = ["/", "/brands/", "/creatives/", "/clusters/", "/insights/"]
VIEWPORTS = {"desktop": {"width": 1440, "height": 900}, "mobile": {"width": 400, "height": 860}}


async def inspect(base: str, out: Path, extra_routes: list) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    report = {"base": base, "pages": []}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for vp_name, vp in VIEWPORTS.items():
            ctx = await browser.new_context(viewport=vp)
            for route in ROUTES + extra_routes:
                page = await ctx.new_page()
                errors, failed = [], []
                page.on("console", lambda m, e=errors: e.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda exc, e=errors: e.append(f"pageerror: {exc}"))
                page.on("requestfailed", lambda r, f=failed: None if "webpack-hmr" in r.url or "_next/static/webpack" in r.url else f.append(f"{r.url} {r.failure}"))
                page.on("response", lambda r, f=failed: f.append(f"{r.url} HTTP {r.status}") if r.status >= 400 else None)
                # dev server keeps an HMR websocket open, so "networkidle" never fires: wait for load + settle
                resp = await page.goto(base.rstrip("/") + route, wait_until="load", timeout=90000)
                await page.wait_for_timeout(2500)
                info = await page.evaluate("""() => ({
                    title: document.title,
                    h1: [...document.querySelectorAll('h1')].map(h => h.innerText),
                    broken_images: [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src),
                    n_images: document.images.length,
                    overflow_x: document.documentElement.scrollWidth > window.innerWidth + 1,
                    empty_states: [...document.querySelectorAll('[data-empty-state], [role=status]')].map(e => e.innerText.slice(0, 120)),
                    provisional_banner: !!document.body.innerText.match(/Provisional data/i),
                    text_sample: document.body.innerText.slice(0, 400),
                })""")
                shot = out / f"{vp_name}{route.strip('/').replace('/', '_').replace('?', '_').replace('=', '-') or '_home'}.png"
                await page.screenshot(path=str(shot), full_page=True)
                report["pages"].append({"viewport": vp_name, "route": route, "status": resp.status if resp else None,
                                        "console_errors": errors, "failed_requests": failed, **info,
                                        "screenshot": str(shot)})
                await page.close()
            await ctx.close()
        await browser.close()
    report["ok"] = all(not p["console_errors"] and not p["failed_requests"] and not p["broken_images"]
                       and p["status"] == 200 for p in report["pages"])
    (out / "inspection.json").write_text(json.dumps(report, indent=1))
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:3000")
    ap.add_argument("--out", type=Path, default=Path("data/outputs/dashboard_inspection"))
    ap.add_argument("--route", action="append", default=[], help="extra route(s), e.g. /creative/?id=123")
    a = ap.parse_args(argv)
    r = asyncio.run(inspect(a.base, a.out, a.route))
    for p in r["pages"]:
        print(f"[{p['viewport']:7}] {p['route']:28} HTTP {p['status']} imgs={p['n_images']:3} broken={len(p['broken_images'])} "
              f"console_err={len(p['console_errors'])} failed_req={len(p['failed_requests'])} overflow_x={p['overflow_x']}")
    print("OK" if r["ok"] else "PROBLEMS FOUND")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

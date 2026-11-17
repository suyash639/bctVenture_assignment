"""
Build the SOP PDF (docs/sop/AdVision_AI_SOP.pdf) from docs/sop/sop_template.html.

Every {{placeholder}} is filled from the repository's current data files, so the PDF always
matches the frozen dataset fingerprint. Rendering uses Playwright's Chromium (already a dependency).

Usage: python scripts/build_sop_pdf.py [--tests-log data/outputs/logs/final_pytest.log]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs/sop/sop_template.html"
OUT_HTML = ROOT / "docs/sop/AdVision_AI_SOP.html"
OUT_PDF = ROOT / "docs/sop/AdVision_AI_SOP.pdf"


def load(p):
    return json.loads((ROOT / p).read_text())


def values(tests_log: Path) -> dict:
    ds = ROOT / "data/processed/validated_dataset.csv"
    sha = hashlib.sha256(ds.read_bytes()).hexdigest()
    frozen = load("data/processed/DATASET_FROZEN.json")
    if frozen["dataset_sha256"] != sha:
        raise SystemExit("dataset is not frozen at its current version; run `make freeze` first")
    rows = list(csv.DictReader(open(ds, encoding="utf-8")))
    ver = [r for r in rows if r["final_status"] == "VERIFIED"]
    fm = load("data/processed/visual_features.json")
    if fm["meta"]["selection"]["dataset_sha256"] != sha:
        raise SystemExit("visual features are stale; run `make features`")
    rm = load("data/outputs/run_manifest.json")
    if rm["summary"]["dataset"]["sha256"] != sha:
        raise SystemExit("analysis outputs are stale; run `make analyze`")
    emb = np.load(ROOT / "data/processed/clip_embeddings.npy")
    mapping = list(csv.DictReader(open(ROOT / "data/quality/replacement_mapping.csv")))
    dups = load("data/quality/duplicate_groups.json")["groups"]

    def sel(v):
        s = load(f"data/outputs/clustering/{v}/selected_configuration.json")
        sw = load(f"data/outputs/clustering/{v}/sweep_results.json")
        e = next(x for x in sw["entries"] if x["config"]["config_id"] == s["selected_config"]["config_id"])
        return s["selected_config"]["config_id"], e
    clip_id, ce = sel("clip")
    fused_id, fe = sel("fused")
    m = ce["metrics"]
    a = list(csv.DictReader(open(ROOT / "data/outputs/clustering/clip/assignments.csv")))
    by = {}
    for r in a:
        by.setdefault(r["cluster_id"], Counter())[r["brand"]] += 1
    purity = sum(max(c.values()) for c in by.values()) / len(a)
    tl = tests_log.read_text().strip().splitlines()[-1] if tests_log.is_file() else "not run"
    passed = re.search(r"(\d+) passed", tl)
    per_brand = Counter(r["brand"] for r in ver)
    sizes = sorted(m["cluster_sizes"].values(), reverse=True)
    return {
        "generated_at": time.strftime("%d %b %Y, %H:%M %Z"),
        "dataset_sha": sha, "frozen_at": frozen["frozen_at"],
        "n_verified": len(ver), "n_excluded": len(rows) - len(ver),
        "per_brand": " · ".join(f"{b} {n}" for b, n in per_brand.items()),
        "n_replaced": sum(1 for x in mapping if x["status"] == "replaced"),
        "n_unresolved": sum(1 for x in mapping if x["status"] != "replaced"),
        "dup_groups": f"{len(dups)} groups ({sum(len(g['members']) for g in dups)} ads; {sum(len(g['members']) - 1 for g in dups)} excluded as duplicates)",
        "features_status": f"{fm['meta']['status_counts']['success']}/{len(fm['records'])} success, "
                           f"{fm['meta']['status_counts']['failed']} failed",
        "clip_model": fm["meta"]["clip"]["model"], "emb_shape": f"{emb.shape[0]} × {emb.shape[1]} (L2-normalised)",
        "clip_config": clip_id, "clip_k": m["n_clusters"], "n_clusters": m["n_clusters"],
        "clip_sizes": ", ".join(map(str, sizes)), "clip_noise": f"{m['n_noise']} noise",
        "clip_metrics": f"{m['silhouette']:.3f} · {m['davies_bouldin']:.3f} · {m['calinski_harabasz']:.2f}",
        "clip_stability": f"{ce['stability']['subsample_ari']:.3f} · {ce['stability']['neighbour_ari']:.3f}",
        "fused_config": f"{fused_id} (silhouette {fe['metrics']['silhouette']:.3f})",
        "brand_purity": f"{purity:.0%}",
        "n_insights": len(load("dashboard/public/data/insights.json")),
        "tests_line": tl, "tests_passed": passed.group(1) if passed else "—",
    }


async def render(html_path: Path, pdf_path: Path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        await page.goto(html_path.resolve().as_uri(), wait_until="load")
        await page.pdf(path=str(pdf_path), format="A4", print_background=True, prefer_css_page_size=True,
                       display_header_footer=True, header_template="<span></span>",
                       footer_template='<div style="width:100%;font-size:8px;color:#6b7280;padding:0 16mm;display:flex;'
                                       'justify-content:space-between"><span>SOP-ADV-001 · AdVision AI · v1.0</span>'
                                       '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
        await b.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests-log", type=Path, default=ROOT / "data/outputs/logs/final_pytest.log")
    a = ap.parse_args(argv)
    vals = values(a.tests_log)
    page = TEMPLATE.read_text()
    for k, v in vals.items():
        page = page.replace("{{" + k + "}}", html.escape(str(v)))
    left = re.findall(r"\{\{(\w+)\}\}", page)
    if left:
        raise SystemExit(f"unfilled placeholders: {left}")
    OUT_HTML.write_text(page)
    asyncio.run(render(OUT_HTML, OUT_PDF))
    print(OUT_PDF, f"{OUT_PDF.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    sys.exit(main())

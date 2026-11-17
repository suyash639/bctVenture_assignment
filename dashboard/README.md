# Meta Ads Creative Intelligence: dashboard

A static Next.js 14 dashboard over the AdVision AI analysis outputs. It **only** reads the JSON
export in `public/data/`, and contains no metrics, sample data or placeholder images of its own.
When the export is missing, every page shows an empty state naming the pipeline step that
produces the missing file.

## Stack

| Package | Version | Notes |
|---|---|---|
| next | 14.2.35 | App Router, `output: "export"` (static site in `out/`) |
| react / react-dom | 18.3.1 | |
| typescript | 5.6.3 | `strict` + `noUncheckedIndexedAccess` |
| tailwindcss | 3.4.14 | slate neutrals + one indigo accent |
| recharts | 2.12.7 | charts |
| vitest / @testing-library/react / jsdom | 2.1.4 / 16.0.1 / 25.0.1 | tests |
| postcss | 8.5.32 | pinned and overridden (patched advisories) |

**Security note:** `npm audit` reports advisories against Next 14. All of them concern the Next
**server runtime**: image optimizer, server actions, middleware, rewrites and RSC request
handling, with fixes only in 15.5+/16. This app is a pure static export, so none of that code
runs in production. Moving to Next 15.5+ remains a recommended follow-up.

## Commands

```bash
cd dashboard
npm install
npm run dev        # http://localhost:3000 (reads public/data/ at runtime)
npm run lint       # next lint
npm run typecheck  # tsc --noEmit
npm test           # vitest (SYNTHETIC fixtures only)
npm run build      # static export -> out/
npm start          # serve out/ locally
```

## Where the data comes from

```bash
# from the repo root, after the dataset is validated (and ideally frozen) and the pipeline has run
python -m src.export.dashboard_data      # writes dashboard/public/data/{manifest,ads,clusters,insights}.json + creatives/
```

The schema is defined in [`../docs/dashboard_data_contract.md`](../docs/dashboard_data_contract.md)
and mirrored in `lib/types.ts`. Data is fetched at runtime, so after re-exporting you only need
to refresh the browser. For a deployed static build, copy `public/data/` into `out/data/` or rebuild.

| File | Required for | If missing |
|---|---|---|
| `manifest.json` | every page (counts, provisional flag, brand order) | Overview shows "No data export yet" |
| `ads.json` | Overview charts, Brands, Creatives, Creative Detail | empty state |
| `clusters.json` | Cluster Explorer, cluster cards | "Clusters not available" |
| `insights.json` | Insights, "insights citing this ad" | "Insights not available" |

## Truthfulness rules (enforced in code)

- `null` always renders as an **Unavailable** badge (`components/ui.tsx: Value/UnavailableValue`). Zero is shown as 0.
- `manifest.provisional === true` shows a persistent **Provisional data: not for citation** banner on every page.
- Only VERIFIED ads are exported, so the UI never shows excluded records. An Ad ID that isn't in
  `ads.json` gets "not in the verified dataset", and an insight citing an unknown ID shows it in red.
- The UI derives only counts, shares and quantiles from `ads.json`, each labelled with its n. Insight
  statements are shown verbatim, and the UI generates no recommendations.
- A failed image shows "Image unavailable", never a substitute picture.
- Test fixtures live only in `tests/fixtures/`, are labelled SYNTHETIC, and are never served.

## Structure

```
app/            pages: / · /brands · /creatives · /clusters · /creative?id= · /insights
components/     Shell (sidebar), DataProvider, Gate, ui (StatCard, ChartCard, BrandBadge, Tag,
                EmptyState, LoadingState, ProvisionalBanner, UnavailableValue, DataTable),
                CreativeCard, ColourSwatchBar, FilterBar, charts/Charts (bar, 100%-stacked, scatter)
lib/            types.ts (contract), data.ts (loaders), filters.ts, stats.ts, palette.ts
tests/          vitest suites + SYNTHETIC fixtures
```

Design rationale: [`../reports/dashboard_design.md`](../reports/dashboard_design.md).

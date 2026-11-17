"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useDashboardData } from "@/components/DataProvider";
import { Gate } from "@/components/Gate";
import { GroupedScatter, StackedShareChart } from "@/components/charts/Charts";
import { BrandBadge, ChartCard, DataTable, EmptyState, PageHeader } from "@/components/ui";
import { brandColour, COLOUR_BUCKETS, seriesColour } from "@/lib/palette";
import { countBy, fmt, meanColourDistribution, quantiles, stableJitter } from "@/lib/stats";
import type { Ad } from "@/lib/types";

const LAYOUTS = ["product_focused", "lifestyle", "testimonial", "offer_heavy", "educational", "unknown"];

export default function BrandsPage() {
  const { loading, data } = useDashboardData();
  return (
    <>
      <PageHeader
        title="Brand Comparison"
        description="Distributions computed directly from the verified ads in the export. Every chart states its n; ads without extracted features are counted as unavailable, never imputed."
      />
      <Gate loading={loading} result={data?.ads} title="Ad records not exported">
        {(ads) => <BrandsBody ads={ads} brands={data?.manifest.data?.brands ?? [...new Set(ads.map((a) => a.brand))]} />}
      </Gate>
    </>
  );
}

/** Share rows (category = brand) for a categorical key; shares over ads where the key is known. */
function shareRows(ads: Ad[], brands: string[], keyOf: (a: Ad) => string | null | undefined, keys: string[]) {
  return brands.map((b) => {
    const mine = ads.filter((a) => a.brand === b);
    const known = mine.filter((a) => keyOf(a) != null);
    const row: { category: string; n: number } & Record<string, number | string> = { category: b, n: known.length };
    for (const k of keys) row[k] = known.length ? known.filter((a) => keyOf(a) === k).length / known.length : 0;
    return row;
  });
}

function BrandsBody({ ads, brands }: { ads: Ad[]; brands: string[] }) {
  const { data } = useDashboardData();
  const featuresAvailable = data?.manifest.data?.available.features ?? ads.some((a) => a.features);
  const withFeatures = ads.filter((a) => a.features);

  const colourRows = useMemo(
    () =>
      brands.map((b) => {
        const { n, shares } = meanColourDistribution(ads.filter((a) => a.brand === b));
        return { category: b, n, ...Object.fromEntries(COLOUR_BUCKETS.map((c) => [c.key, shares[c.key] ?? 0])) } as { category: string; n: number } & Record<string, number | string>;
      }),
    [ads, brands],
  );
  const formats = [...new Set(ads.map((a) => a.format).filter(Boolean))] as string[];
  const ctas = countBy(ads, (a) => a.cta_normalised ?? a.cta).map((r) => r.key);

  return (
    <div className="space-y-6">
      <section aria-label="Brand summary" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {brands.map((b) => {
          const mine = ads.filter((a) => a.brand === b);
          return (
            <div key={b} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
              <BrandBadge brand={b} />
              <p className="mt-2 text-2xl font-semibold tabular-nums">{mine.length}</p>
              <p className="text-xs text-slate-500">verified ads</p>
            </div>
          );
        })}
      </section>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard id="format" title="Creative format by brand" subtitle="Share of each brand's verified ads">
          <StackedShareChart rows={shareRows(ads, brands, (a) => a.format, formats)} series={formats.map((f, i) => ({ key: f, label: f, colour: seriesColour(i) }))} caption="Format share per brand" />
        </ChartCard>
        <ChartCard id="cta" title="Call-to-action by brand" subtitle="CTA text as shown on the live Ad Library card (case-normalised)">
          <StackedShareChart
            rows={shareRows(ads, brands, (a) => a.cta_normalised ?? a.cta, ctas)}
            series={ctas.map((c, i) => ({ key: c, label: c, colour: seriesColour(i) }))}
            caption="CTA share per brand"
          />
        </ChartCard>
      </div>

      {!featuresAvailable || withFeatures.length === 0 ? (
        <EmptyState title="Visual features not available" reason="Colour, layout and text-density comparisons appear after feature extraction has run on the frozen dataset and been exported." />
      ) : (
        <>
          <ChartCard id="colour" title="Colour distribution by brand" subtitle="Mean share of pixels per colour bucket (white / grey / black + 12 hue bins), over ads with features">
            <StackedShareChart rows={colourRows} series={COLOUR_BUCKETS.map((c) => ({ key: c.key, label: c.label, colour: c.hex }))} caption="Mean colour bucket share per brand" />
          </ChartCard>

          <ChartCard id="swatches" title="Dominant colour of each creative" subtitle="One swatch per ad: its largest k-means colour. Select a swatch to open the creative.">
            <div className="space-y-2">
              {brands.map((b) => {
                const mine = withFeatures.filter((a) => a.brand === b);
                return (
                  <div key={b} className="flex items-center gap-3">
                    <div className="w-40 shrink-0"><BrandBadge brand={b} /></div>
                    <ul className="flex flex-wrap gap-1" aria-label={`Dominant colours for ${b}`}>
                      {mine.map((a) => {
                        const c = a.features!.dominant_colours[0];
                        return (
                          <li key={a.ad_id}>
                            <Link
                              href={`/creative/?id=${a.ad_id}`}
                              title={`${a.ad_id}: ${c?.hex ?? "unavailable"} (${c ? (100 * c.proportion).toFixed(0) : "—"}%)`}
                              className="block h-6 w-6 rounded border border-slate-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500"
                              style={{ backgroundColor: c?.hex ?? "transparent" }}
                            >
                              <span className="sr-only">{a.ad_id}</span>
                            </Link>
                          </li>
                        );
                      })}
                      {mine.length === 0 ? <li className="text-xs text-slate-500">No ads with features</li> : null}
                    </ul>
                  </div>
                );
              })}
            </div>
          </ChartCard>

          <div className="grid gap-4 xl:grid-cols-2">
            <ChartCard id="layout" title="Layout category by brand" subtitle="Rule-based heuristic labels (see methodology) — descriptive, not validated against human labels">
              <StackedShareChart
                rows={shareRows(withFeatures, brands, (a) => a.features?.layout_category, LAYOUTS)}
                series={LAYOUTS.map((l, i) => ({ key: l, label: l.replace(/_/g, " "), colour: l === "unknown" ? "#cbd5e1" : seriesColour(i) }))}
                caption="Layout share per brand"
              />
            </ChartCard>
            <ChartCard id="orientation" title="Orientation by brand" subtitle="square = |w/h − 1| ≤ 5%">
              <StackedShareChart
                rows={shareRows(withFeatures, brands, (a) => a.features?.orientation, ["portrait", "square", "landscape"])}
                series={["portrait", "square", "landscape"].map((o, i) => ({ key: o, label: o, colour: seriesColour(i + 4) }))}
                caption="Orientation share per brand"
              />
            </ChartCard>
          </div>

          <TextDensity ads={withFeatures} brands={brands} />
        </>
      )}
    </div>
  );
}

function TextDensity({ ads, brands }: { ads: Ad[]; brands: string[] }) {
  const points = ads
    .filter((a) => a.features?.text_density != null)
    .map((a) => ({ id: a.ad_id, x: brands.indexOf(a.brand) + 0.5 * stableJitter(a.ad_id), y: a.features!.text_density as number, group: a.brand }));
  const missing = ads.filter((a) => a.features?.text_density == null).map((a) => a.ad_id);
  return (
    <ChartCard
      id="text"
      title="On-image text density by brand"
      subtitle="Share of the image covered by OCR-detected text boxes; one point per ad (horizontal offset is a fixed per-ad jitter for legibility)"
      footer={missing.length ? `Text density unavailable for ${missing.length} ad(s): ${missing.join(", ")}` : undefined}
    >
      {points.length === 0 ? (
        <EmptyState title="Text density unavailable" reason="OCR features were not extracted for these ads." />
      ) : (
        <>
          <GroupedScatter
            points={points}
            groups={brands.map((b) => ({ key: b, label: b, colour: brandColour(b, brands) }))}
            xLabel="Brand"
            yLabel="Text density"
            xTicks={brands.map((_, i) => i)}
            xTickFormatter={(v) => brands[Math.round(v)] ?? ""}
            caption="Text density per ad"
            height={300}
          />
          <DataTable
            caption="Text density quantiles per brand"
            headers={["Brand", "n", "min", "Q1", "median", "Q3", "max"]}
            rows={brands.map((b) => {
              const q = quantiles(points.filter((p) => p.group === b).map((p) => p.y));
              return q ? [b, q.n, fmt(q.min), fmt(q.q1), fmt(q.median), fmt(q.q3), fmt(q.max)] : [b, 0, "—", "—", "—", "—", "—"];
            })}
          />
        </>
      )}
    </ChartCard>
  );
}

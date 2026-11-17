"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, type ReactNode } from "react";
import { ColourSwatchBar } from "@/components/ColourSwatchBar";
import { CreativeImage } from "@/components/CreativeCard";
import { useDashboardData } from "@/components/DataProvider";
import { BrandBadge, ChartCard, EmptyState, LoadingState, PageHeader, Tag, UnavailableValue, Value } from "@/components/ui";
import { fmt } from "@/lib/stats";
import type { Ad } from "@/lib/types";

export default function CreativePage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <CreativeInner />
    </Suspense>
  );
}

function CreativeInner() {
  const params = useSearchParams();
  const id = params?.get("id") ?? "";
  const { loading, data, adIndex } = useDashboardData();
  if (loading) return <LoadingState />;
  if (!data || data.ads.status !== "ok") {
    return <EmptyState title="Ad records not exported" reason={data?.ads.reason} />;
  }
  if (!id) {
    return <EmptyState title="No creative selected" reason="Open a creative from the Creatives list, a cluster, or an insight." action={<Link className="text-sm text-accent-700 hover:underline" href="/creatives/">Browse creatives</Link>} />;
  }
  const ad = adIndex.get(id);
  if (!ad) {
    return <EmptyState title={`Ad ${id} is not in the verified dataset`} reason="Only VERIFIED ads are exported. Excluded or unknown IDs are not shown." />;
  }
  const citing = (data.insights.data ?? []).filter((o) => o.supporting_ad_ids.includes(id));
  return <CreativeDetail ad={ad} citing={citing.map((o) => ({ id: o.observation_id, statement: o.statement }))} />;
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[9rem_1fr] gap-3 border-b border-slate-100 py-2 text-sm last:border-0">
      <dt className="text-slate-500">{label}</dt>
      <dd className="min-w-0 break-words text-slate-800">{children}</dd>
    </div>
  );
}

function CreativeDetail({ ad, citing }: { ad: Ad; citing: { id: string; statement: string }[] }) {
  const f = ad.features;
  return (
    <>
      <PageHeader title={`Ad ${ad.ad_id}`} description={<span className="inline-flex items-center gap-2"><BrandBadge brand={ad.brand} /> {ad.advertiser}</span>}>
        <a
          href={ad.ad_library_url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500"
        >
          View in Meta Ad Library ↗
        </a>
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <figure className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
          <CreativeImage ad={ad} className="max-h-[70vh] w-full" />
          <figcaption className="mt-2 text-xs text-slate-500">
            Creative as served on the live Ad Library card{ad.image_type === "video_thumbnail" ? " (video poster frame)" : ""}.
            {f ? ` ${f.width}×${f.height}px, not resized.` : ""}
          </figcaption>
        </figure>

        <div className="space-y-4">
          <ChartCard id="meta" title="Ad metadata" subtitle="From the live Ad Library card for this exact Library ID">
            <dl>
              <Row label="Library ID"><span className="font-mono">{ad.ad_id}</span></Row>
              <Row label="Advertiser">{ad.advertiser} <Tag>{ad.advertiser_type.replace(/_/g, " ")}</Tag></Row>
              <Row label="Status"><Value v={ad.status} /></Row>
              <Row label="Active dates"><Value v={ad.start_date}>{ad.start_date}{ad.end_date ? ` – ${ad.end_date}` : " – (still running at verification)"}</Value></Row>
              <Row label="Format"><Value v={ad.format} /> {ad.image_type ? <Tag>{ad.image_type.replace(/_/g, " ")}</Tag> : null}</Row>
              <Row label="Ad copy"><Value v={ad.body}><span className="whitespace-pre-line">{ad.body}</span></Value></Row>
              <Row label="Headline"><Value v={ad.link_headline} /></Row>
              <Row label="Link caption"><Value v={ad.link_caption} /></Row>
              <Row label="CTA"><Value v={ad.cta} /></Row>
              <Row label="Landing page">
                <Value v={ad.landing_url}>
                  <a href={ad.landing_url ?? undefined} target="_blank" rel="noopener noreferrer nofollow" className="text-accent-700 hover:underline">{ad.landing_url}</a>
                </Value>
              </Row>
              <Row label="Record origin">
                {ad.record_origin}
                {ad.replaces_ad_id ? <> · replaces <span className="font-mono">{ad.replaces_ad_id}</span></> : null}
              </Row>
              <Row label="Cluster">
                {ad.cluster ? (
                  ad.cluster.is_noise ? <Link className="text-accent-700 hover:underline" href="/clusters/?c=noise">Noise</Link> : (
                    <Link className="text-accent-700 hover:underline" href={`/clusters/?c=${ad.cluster.cluster_id}`}>Cluster {ad.cluster.cluster_id}</Link>
                  )
                ) : <UnavailableValue reason="Clustering not run or ad not clustered" />}
              </Row>
            </dl>
          </ChartCard>

          <ChartCard id="features" title="Extracted visual features" subtitle="Computed from the image pixels (src/vision)">
            {f ? (
              <dl>
                <Row label="Dimensions">{f.width}×{f.height}px · {f.orientation} · aspect {fmt(f.aspect_ratio)}</Row>
                <Row label="Dominant colours">
                  <ColourSwatchBar colours={f.dominant_colours} label={`Dominant colours of ad ${ad.ad_id}`} />
                  <span className="mt-1 block font-mono text-xs text-slate-500">{f.dominant_colours.map((c) => `${c.hex} ${(100 * c.proportion).toFixed(0)}%`).join(" · ")}</span>
                </Row>
                <Row label="Brightness">{fmt(f.brightness)}</Row>
                <Row label="Contrast">{fmt(f.contrast)}</Row>
                <Row label="Sharpness">{fmt(f.sharpness, 1)}</Row>
                <Row label="Colourfulness">{fmt(f.colourfulness, 1)}</Row>
                <Row label="Text density"><Value v={f.text_density}>{fmt(f.text_density)}</Value> {f.text_position ? <Tag>{f.text_position}</Tag> : null}</Row>
                <Row label="On-image text (OCR)"><Value v={f.ocr_text}><span className="text-xs">{f.ocr_text}</span></Value></Row>
                <Row label="Layout (heuristic)">
                  <Value v={f.layout_category}>{f.layout_category?.replace(/_/g, " ")}</Value>
                  {f.layout_reasons?.length ? <ul className="mt-1 list-disc pl-4 text-xs text-slate-500">{f.layout_reasons.map((r) => <li key={r}>{r}</li>)}</ul> : null}
                </Row>
              </dl>
            ) : (
              <EmptyState title="Features not extracted" reason="Visual features appear after feature extraction has run and been exported." />
            )}
          </ChartCard>

          <ChartCard id="cited" title="Insights citing this ad">
            {citing.length ? (
              <ul className="space-y-2 text-sm">
                {citing.map((o) => (
                  <li key={o.id}><Link href={`/insights/#${o.id}`} className="text-accent-700 hover:underline">{o.statement}</Link></li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No exported observation cites this ad.</p>
            )}
          </ChartCard>
        </div>
      </div>
    </>
  );
}

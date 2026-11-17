"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, type ReactNode } from "react";
import { CreativeCard } from "@/components/CreativeCard";
import { useDashboardData } from "@/components/DataProvider";
import { Gate } from "@/components/Gate";
import { CountBarChart, GroupedScatter } from "@/components/charts/Charts";
import { ChartCard, EmptyState, LoadingState, PageHeader, Tag, UnavailableValue } from "@/components/ui";
import { brandColour, NOISE_COLOUR, seriesColour } from "@/lib/palette";
import { fmt } from "@/lib/stats";
import type { Ad, ClustersFile, ClusterSummary } from "@/lib/types";

export default function ClustersPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <ClustersInner />
    </Suspense>
  );
}

function ClustersInner() {
  const { loading, data, adIndex } = useDashboardData();
  return (
    <>
      <PageHeader
        title="Cluster Explorer"
        description="Unsupervised groups of visually similar creatives (CLIP embeddings, optionally fused with colour/layout/text features). Noise points are shown separately, never forced into a cluster."
      />
      <Gate loading={loading} result={data?.clusters} title="Clusters not available">
        {(clusters) => <ClustersBody clusters={clusters} adIndex={adIndex} />}
      </Gate>
    </>
  );
}

const clusterKey = (c: { cluster_id: number; is_noise: boolean }) => (c.is_noise ? "noise" : String(c.cluster_id));
const clusterLabel = (c: { cluster_id: number; is_noise: boolean }) => (c.is_noise ? "Noise" : `Cluster ${c.cluster_id}`);

function ClustersBody({ clusters, adIndex }: { clusters: ClustersFile; adIndex: Map<string, Ad> }) {
  const router = useRouter();
  const params = useSearchParams();
  const ordered = useMemo(() => [...clusters.clusters].sort((a, b) => Number(a.is_noise) - Number(b.is_noise) || b.size - a.size), [clusters]);
  const selectedKey = params?.get("c") ?? (ordered[0] ? clusterKey(ordered[0]) : null);
  const selected = ordered.find((c) => clusterKey(c) === selectedKey || String(c.cluster_id) === selectedKey) ?? ordered[0];
  const groups = ordered.map((c, i) => ({ key: clusterKey(c), label: clusterLabel(c), colour: c.is_noise ? NOISE_COLOUR : seriesColour(i) }));
  const groupOf = new Map<string, string>();
  for (const c of ordered) for (const id of c.ad_ids) groupOf.set(id, clusterKey(c));

  const projection = clusters.projection;
  const unknownIds = (projection ?? []).filter((p) => !groupOf.has(p.ad_id)).map((p) => p.ad_id);

  return (
    <div className="space-y-6">
      <ChartCard id="selection" title="Selected clustering configuration" subtitle={clusters.selected.config_id}>
        <div className="flex flex-wrap gap-2 text-xs">
          <Tag tone="accent">{clusters.selected.algorithm}</Tag>
          <Tag>{clusters.metrics.n_clusters} clusters</Tag>
          <Tag>{clusters.metrics.n_noise} noise</Tag>
          <Tag>Silhouette {fmt(clusters.metrics.silhouette)}</Tag>
          <Tag>Davies–Bouldin {fmt(clusters.metrics.davies_bouldin)}</Tag>
          <Tag>Calinski–Harabasz {fmt(clusters.metrics.calinski_harabasz, 1)}</Tag>
        </div>
        <p className="mt-3 whitespace-pre-line text-sm text-slate-700">{clusters.selected.rationale}</p>
        {clusters.selected.warnings.length ? (
          <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-amber-800">
            {clusters.selected.warnings.map((w) => <li key={w}>{w}</li>)}
          </ul>
        ) : null}
      </ChartCard>

      <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
        <nav aria-label="Clusters" className="rounded-lg border border-slate-200 bg-white p-2 shadow-sm">
          <ul className="space-y-1">
            {ordered.map((c, i) => {
              const active = c === selected;
              return (
                <li key={clusterKey(c)}>
                  <button
                    type="button"
                    aria-pressed={active}
                    onClick={() => router.replace(`/clusters/?c=${clusterKey(c)}`, { scroll: false })}
                    className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 ${active ? "bg-accent-50 text-accent-700" : "hover:bg-slate-50"}`}
                  >
                    <span className="flex items-center gap-2">
                      <span aria-hidden className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: c.is_noise ? NOISE_COLOUR : seriesColour(i) }} />
                      {clusterLabel(c)}
                    </span>
                    <span className="tabular-nums text-xs text-slate-500">{c.size}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>
        {selected ? <ClusterDetail cluster={selected} adIndex={adIndex} /> : <EmptyState title="No clusters in the export" />}
      </div>

      <ChartCard
        id="pca"
        title="2-D projection (PCA)"
        subtitle="Each point is one verified ad; select a point to open its creative. PCA preserves only part of the variance — distances here are approximate."
        footer={unknownIds.length ? `${unknownIds.length} projected ad(s) have no cluster entry: ${unknownIds.join(", ")}` : undefined}
      >
        {projection && projection.length ? (
          <GroupedScatter
            points={projection.map((p) => ({ id: p.ad_id, x: p.x, y: p.y, group: groupOf.get(p.ad_id) ?? "unassigned" }))}
            groups={unknownIds.length ? [...groups, { key: "unassigned", label: "Unassigned", colour: "#e2e8f0" }] : groups}
            xLabel="PC1"
            yLabel="PC2"
            caption="PCA projection of verified ads"
            highlight={selected ? clusterKey(selected) : null}
            onPointClick={(id) => router.push(`/creative/?id=${encodeURIComponent(id)}`)}
          />
        ) : (
          <EmptyState title="Projection not available" reason="The export has no 2-D projection for this run." />
        )}
      </ChartCard>

      <ChartCard id="sizes" title="Cluster sizes">
        <CountBarChart
          rows={ordered.map((c) => ({ key: c.is_noise ? "Noise" : `C${c.cluster_id}`, count: c.size }))}
          xLabel="Cluster"
          colourFor={(k, i) => (k === "Noise" ? NOISE_COLOUR : seriesColour(i))}
          caption="Ads per cluster"
        />
      </ChartCard>
    </div>
  );
}

function ClusterDetail({ cluster, adIndex }: { cluster: ClusterSummary; adIndex: Map<string, Ad> }) {
  const members = cluster.ad_ids.map((id) => ({ id, ad: adIndex.get(id) }));
  const missing = members.filter((m) => !m.ad).map((m) => m.id);
  const reps = new Set(cluster.representative_ad_ids);
  const brandRows = Object.entries(cluster.brand_mix).sort((a, b) => b[1] - a[1]);
  return (
    <section aria-label={`${clusterLabel(cluster)} details`} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <ChartCard id="mix" title={`${clusterLabel(cluster)} · brand mix`} subtitle={`${cluster.size} ads`}>
          <ul className="space-y-1.5">
            {brandRows.map(([b, n]) => (
              <li key={b} className="flex items-center gap-2 text-sm">
                <span className="w-36 truncate">{b}</span>
                <span className="h-2 rounded" style={{ width: `${(100 * n) / cluster.size}%`, backgroundColor: brandColour(b) }} aria-hidden />
                <span className="tabular-nums text-xs text-slate-500">{n}</span>
              </li>
            ))}
          </ul>
        </ChartCard>
        <ChartCard id="profile" title="Cluster characteristics" subtitle="Computed profile from the intelligence stage">
          {Object.keys(cluster.profile).length ? (
            <dl className="grid grid-cols-1 gap-y-2 text-sm">
              {Object.entries(cluster.profile)
                .filter(([k]) => !HIDDEN_PROFILE_KEYS.has(k))
                .map(([k, v]) => (
                  <div key={k} className="grid grid-cols-1 gap-1 sm:grid-cols-[9rem_minmax(0,1fr)] sm:gap-2">
                    <dt className="text-xs text-slate-500">{PROFILE_LABELS[k] ?? k.replace(/_/g, " ")}</dt>
                    <dd className="min-w-0 text-xs text-slate-800">{renderProfileValue(k, v)}</dd>
                  </div>
                ))}
            </dl>
          ) : (
            <UnavailableValue reason="No profile exported for this cluster" />
          )}
        </ChartCard>
      </div>
      <ChartCard id="members" title="Creatives" subtitle="Representatives (closest to the cluster centre) are outlined">
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {[...members]
            .sort((a, b) => Number(reps.has(b.id)) - Number(reps.has(a.id)))
            .map((m) => (m.ad ? <li key={m.id}><CreativeCard ad={m.ad} highlight={reps.has(m.id)} /></li> : null))}
        </ul>
        {missing.length ? <p className="mt-2 text-xs text-red-700">Not found in ads.json: {missing.join(", ")}</p> : null}
      </ChartCard>
    </section>
  );
}

const HIDDEN_PROFILE_KEYS = new Set(["cluster", "size", "brand_mix"]); // shown in the header / brand-mix card
const PROFILE_LABELS: Record<string, string> = {
  layout_mix: "Layout labels (heuristic)",
  orientation_mix: "Orientation",
  cta_mix: "CTA",
  mean_text_density: "Mean text density",
  mean_colour_families: "Colour families (mean share)",
  distinguishing_features: "Distinguishing features",
};

function fmtNum(v: number): string {
  return Number.isInteger(v) ? String(v) : Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(3);
}

function Chips({ entries }: { entries: [string, string][] }) {
  return (
    <ul className="flex flex-wrap gap-1">
      {entries.map(([k, v]) => (
        <li key={k} className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5">
          {k.replace(/_/g, " ")} <span className="font-semibold tabular-nums">{v}</span>
        </li>
      ))}
    </ul>
  );
}

/** Renders the intelligence-stage profile values as readable text; values are shown, never altered. */
function renderProfileValue(key: string, v: unknown): ReactNode {
  if (v === null || v === undefined) return <UnavailableValue />;
  if (typeof v === "number") return <span className="tabular-nums">{fmtNum(v)}</span>;
  if (typeof v === "string") return v;
  if (key === "mean_colour_families" && typeof v === "object" && !Array.isArray(v)) {
    const top = Object.entries(v as Record<string, number>).sort((a, b) => b[1] - a[1]).filter(([, x]) => x > 0);
    return <Chips entries={top.map(([k, x]) => [k, `${(100 * x).toFixed(1)}%`])} />;
  }
  if (Array.isArray(v)) {
    return (
      <ul className="space-y-0.5">
        {v.map((f, i) => {
          const d = f as { feature?: string; cluster_mean?: number; dataset_mean?: number; z?: number };
          if (d && typeof d === "object" && d.feature !== undefined) {
            return (
              <li key={i}>
                <span className="font-medium">{d.feature.replace(/_/g, " ")}</span>:{" "}
                <span className="tabular-nums">{fmtNum(d.cluster_mean ?? NaN)}</span> vs{" "}
                <span className="tabular-nums">{fmtNum(d.dataset_mean ?? NaN)}</span> overall (z{" "}
                <span className="tabular-nums">{(d.z ?? 0) >= 0 ? "+" : ""}{(d.z ?? 0).toFixed(2)}</span>)
              </li>
            );
          }
          return <li key={i} className="break-words">{JSON.stringify(f)}</li>;
        })}
      </ul>
    );
  }
  if (typeof v === "object") {
    return <Chips entries={Object.entries(v as Record<string, unknown>).map(([k, x]) => [k, String(x)])} />;
  }
  return String(v);
}

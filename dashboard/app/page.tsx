"use client";

import Link from "next/link";
import { useDashboardData } from "@/components/DataProvider";
import { Gate } from "@/components/Gate";
import { CountBarChart } from "@/components/charts/Charts";
import { ChartCard, EmptyState, PageHeader, StatCard, Tag, UnavailableValue } from "@/components/ui";
import { ExecutiveWalkthrough } from "@/components/ExecutiveWalkthrough";
import { brandColour, NOISE_COLOUR, seriesColour } from "@/lib/palette";
import { countBy, fmt } from "@/lib/stats";
import {
  getVerifiedAdsExplanation,
  getBrandCoverageExplanation,
  getExcludedRecordsExplanation,
  getClustersKPIExplanation,
  getBrandDistributionExplanation,
  getFormatDistributionExplanation,
  getDeliveryStatusExplanation,
  getClusteringMetricsExplanation,
} from "@/lib/explanations";
import type { Ad, ClusterSummary, ClustersFile, Manifest } from "@/lib/types";

export default function OverviewPage() {
  const { loading, data } = useDashboardData();
  return (
    <>
      <PageHeader
        title="Meta Ads Creative Intelligence Platform"
        description="Self-explanatory competitive intelligence for Indian wellness, D2C, and fitness brands. Every advertisement shown has undergone forensic verification; excluded records are transparently tracked to protect computer vision accuracy."
      />
      <Gate loading={loading} result={data?.manifest} title="No data export yet">
        {(manifest) => <OverviewBody manifest={manifest} />}
      </Gate>
    </>
  );
}

function OverviewBody({ manifest }: { manifest: Manifest }) {
  const { data } = useDashboardData();
  const ads = data?.ads.data ?? null;
  const clusters = data?.clusters.data ?? null;
  const mismatch = ads !== null && ads.length !== manifest.dataset.n_verified;

  return (
    <div className="space-y-6">
      {/* Executive Walkthrough: How to Read This Dashboard */}
      <ExecutiveWalkthrough defaultExpanded={false} />

      {/* KPI Cards with 6-Pillar Interactive Explanations */}
      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Verified ads"
          value={manifest.dataset.n_verified}
          hint={manifest.dataset.frozen ? `Frozen ${manifest.dataset.frozen_at?.slice(0, 10) ?? ""}` : "Dataset not frozen"}
          explanation={getVerifiedAdsExplanation(manifest)}
        />
        <StatCard
          label="Brands analyzed"
          value={manifest.brands.length}
          hint={`${Object.keys(manifest.dataset.per_brand || {}).length} monitored competitors`}
          explanation={getBrandCoverageExplanation(manifest)}
        />
        <StatCard
          label="Excluded records"
          value={manifest.dataset.n_excluded}
          hint="Rejected during quality & forensic checks"
          explanation={getExcludedRecordsExplanation(manifest)}
        />
        <StatCard
          label="Visual clusters"
          value={clusters ? clusters.metrics.n_clusters : <UnavailableValue reason={data?.clusters.reason ?? undefined} />}
          hint={clusters ? `${clusters.metrics.n_noise} noise · ${clusters.selected.algorithm}` : "Clustering not run yet"}
          explanation={getClustersKPIExplanation(clusters)}
        />
      </dl>

      {mismatch ? (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          ads.json contains {ads!.length} ads but the manifest reports {manifest.dataset.n_verified} verified. Re-run the exporter.
        </p>
      ) : null}

      {ads === null ? (
        <EmptyState title="Ad records not exported" reason={data?.ads.reason} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <ChartCard
            id="brands"
            title="Verified ads by brand"
            subtitle={`n = ${ads.length} verified creatives`}
            explanation={getBrandDistributionExplanation(ads, manifest.brands)}
          >
            <CountBarChart
              rows={orderBy(countBy(ads, (a) => a.brand), manifest.brands)}
              xLabel="Brand"
              colourFor={(k) => brandColour(k, manifest.brands)}
              caption="Verified ads per brand"
            />
          </ChartCard>

          <ChartCard
            id="format"
            title="Creative format"
            subtitle={`n = ${ads.length} · 100% full-resolution static ads`}
            explanation={getFormatDistributionExplanation(ads)}
          >
            <CountBarChart
              rows={countBy(ads, (a) => a.format)}
              xLabel="Format"
              colourFor={(_, i) => seriesColour(i)}
              caption="Ads per creative format"
            />
          </ChartCard>

          <ChartCard
            id="status"
            title="Delivery status at verification"
            subtitle={`n = ${ads.length} · live auction state`}
            explanation={getDeliveryStatusExplanation(ads)}
          >
            <CountBarChart
              rows={countBy(ads, (a) => a.status)}
              xLabel="Status"
              colourFor={(_, i) => seriesColour(i + 3)}
              caption="Ads per active/inactive status"
            />
          </ChartCard>
        </div>
      )}

      {/* Cluster Overview Card */}
      <ChartCard
        id="clusters"
        title="Visual cluster overview"
        subtitle={clusters ? `Selected configuration: ${clusters.selected.config_id}` : undefined}
        explanation={clusters ? getClusteringMetricsExplanation(clusters) : undefined}
      >
        {clusters && ads ? (
          <ClusterOverview
            clusters={clusters.clusters}
            adsById={new Map(ads.map((a) => [a.ad_id, a]))}
            metrics={clusters.metrics}
            clustersFile={clusters}
          />
        ) : (
          <EmptyState
            title="Clusters not available"
            reason={data?.clusters.reason ?? "Clustering has not been run on the frozen dataset."}
          />
        )}
      </ChartCard>

      {manifest.pipeline ? (
        <p className="text-xs text-slate-500">
          Pipeline run {manifest.pipeline.run_at ?? "—"} · features: {manifest.pipeline.feature_variant ?? "—"} · embeddings: {manifest.pipeline.clip_model ?? "—"}
        </p>
      ) : null}
    </div>
  );
}

function orderBy(rows: { key: string; count: number }[], order: string[]) {
  return [...rows].sort((a, b) => {
    const ia = order.indexOf(a.key);
    const ib = order.indexOf(b.key);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
}

function ClusterOverview({
  clusters,
  adsById,
  metrics,
  clustersFile,
}: {
  clusters: ClusterSummary[];
  adsById: Map<string, Ad>;
  metrics: { silhouette: number | null; davies_bouldin: number | null; calinski_harabasz: number | null };
  clustersFile: ClustersFile;
}) {
  return (
    <div className="space-y-4">
      {/* Educational metrics explainer */}
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Silhouette Score</span>
            <Tag tone="accent">{fmt(metrics.silhouette)}</Tag>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 leading-tight">
            Measures cluster cohesion vs separation (-1 to +1). Positive score confirms real visual grouping beyond noise.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Davies–Bouldin Index</span>
            <Tag tone="neutral">{fmt(metrics.davies_bouldin)}</Tag>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 leading-tight">
            Measures cluster overlap (lower is better). A score near 2.0 indicates clean separation between visual archetypes.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Calinski–Harabasz</span>
            <Tag tone="neutral">{fmt(metrics.calinski_harabasz, 1)}</Tag>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 leading-tight">
            Variance ratio criterion (higher is better). Ratio of between-cluster to within-cluster variance.
          </p>
        </div>
      </div>

      <CountBarChart
        rows={clusters.map((c) => ({ key: c.is_noise ? "Noise" : `C${c.cluster_id}`, count: c.size }))}
        xLabel="Cluster"
        colourFor={(k, i) => (k === "Noise" ? NOISE_COLOUR : seriesColour(i))}
        caption="Ads per cluster"
      />

      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {clusters.map((c) => (
          <li key={c.cluster_id} className="flex items-center gap-3 rounded-md border border-slate-200 p-2 bg-white hover:border-accent-300 transition-colors">
            <div className="flex -space-x-2 shrink-0">
              {c.representative_ad_ids.slice(0, 3).map((id) => {
                const ad = adsById.get(id);
                return ad ? (
                  <img
                    key={id}
                    src={ad.image}
                    alt={`${ad.brand} ${id}`}
                    className="h-10 w-10 rounded border-2 border-white bg-slate-100 object-cover shadow-2xs"
                  />
                ) : null;
              })}
            </div>
            <div className="min-w-0 text-xs flex-1">
              <Link href={`/clusters/?c=${c.cluster_id}`} className="font-semibold text-accent-700 hover:underline block truncate">
                {c.is_noise ? "Noise Group" : `Cluster ${c.cluster_id}`}
              </Link>
              <p className="text-slate-500 text-[11px]">
                {c.size} ads · {Object.keys(c.brand_mix).length} {Object.keys(c.brand_mix).length === 1 ? "brand" : "brands"}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

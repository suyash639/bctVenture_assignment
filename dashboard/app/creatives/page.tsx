"use client";

import { useMemo, useState } from "react";
import { CreativeCard } from "@/components/CreativeCard";
import { useDashboardData } from "@/components/DataProvider";
import { FilterBar } from "@/components/FilterBar";
import { Gate } from "@/components/Gate";
import { EmptyState, PageHeader } from "@/components/ui";
import { EMPTY_FILTER, filterAds } from "@/lib/filters";
import type { Ad } from "@/lib/types";

export default function CreativesPage() {
  const { loading, data } = useDashboardData();
  return (
    <>
      <PageHeader title="Creatives" description="Every verified creative in the export. Search matches Ad ID, brand, advertiser, ad copy, CTA and on-image (OCR) text." />
      <Gate loading={loading} result={data?.ads} title="Ad records not exported">
        {(ads) => <CreativesBody ads={ads} brands={data?.manifest.data?.brands ?? []} />}
      </Gate>
    </>
  );
}

function CreativesBody({ ads, brands }: { ads: Ad[]; brands: string[] }) {
  const [filter, setFilter] = useState(EMPTY_FILTER);
  const options = useMemo(() => {
    const uniq = (xs: (string | null | undefined)[]) => [...new Set(xs.filter((x): x is string => !!x))].sort();
    const clusterIds = uniq(ads.filter((a) => a.cluster && !a.cluster.is_noise).map((a) => String(a.cluster!.cluster_id))).sort((a, b) => Number(a) - Number(b));
    const extras = [ads.some((a) => a.cluster?.is_noise) ? "noise" : null, ads.some((a) => !a.cluster) ? "unassigned" : null].filter((x): x is string => !!x);
    const layouts = uniq(ads.map((a) => a.features?.layout_category));
    return {
      brands: brands.length ? brands : uniq(ads.map((a) => a.brand)),
      formats: uniq(ads.map((a) => a.format)),
      layouts: ads.some((a) => !a.features?.layout_category) ? [...layouts, "unavailable"] : layouts,
      clusters: [...clusterIds, ...extras],
    };
  }, [ads, brands]);
  const shown = filterAds(ads, filter);
  return (
    <>
      <FilterBar value={filter} onChange={setFilter} options={options} resultCount={shown.length} total={ads.length} />
      {shown.length ? (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {shown.map((a) => <li key={a.ad_id}><CreativeCard ad={a} /></li>)}
        </ul>
      ) : (
        <EmptyState title="No creatives match these filters" reason="Adjust the search or reset the filters." />
      )}
    </>
  );
}

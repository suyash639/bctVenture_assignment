import type { Ad } from "./types";

export interface AdFilter {
  query: string;
  brand: string; // "all" or a brand name
  format: string; // "all" | "static" | "carousel" | "video"
  layout: string; // "all" | layout_category | "unavailable"
  cluster: string; // "all" | "noise" | "unassigned" | "<cluster_id>"
}

export const EMPTY_FILTER: AdFilter = { query: "", brand: "all", format: "all", layout: "all", cluster: "all" };

/** Text fields searched by the free-text query (case-insensitive substring). */
function haystack(a: Ad): string {
  return [a.ad_id, a.brand, a.advertiser, a.body, a.link_headline, a.cta, a.features?.ocr_text]
    .filter(Boolean)
    .join("\n")
    .toLowerCase();
}

export function matchesFilter(a: Ad, f: AdFilter): boolean {
  if (f.brand !== "all" && a.brand !== f.brand) return false;
  if (f.format !== "all" && a.format !== f.format) return false;
  if (f.layout !== "all") {
    const layout = a.features?.layout_category ?? "unavailable";
    if (layout !== f.layout) return false;
  }
  if (f.cluster !== "all") {
    if (f.cluster === "unassigned") {
      if (a.cluster !== null) return false;
    } else if (f.cluster === "noise") {
      if (!a.cluster?.is_noise) return false;
    } else if (!a.cluster || a.cluster.is_noise || String(a.cluster.cluster_id) !== f.cluster) {
      return false;
    }
  }
  const q = f.query.trim().toLowerCase();
  return q === "" || haystack(a).includes(q);
}

export const filterAds = (ads: Ad[], f: AdFilter): Ad[] => ads.filter((a) => matchesFilter(a, f));

/** Observation scope family: "brand:Kapiva" -> "brand", "cluster:3" -> "cluster", "dataset" -> "dataset". */
export const scopeKind = (scope: string): string => scope.split(":")[0] ?? scope;

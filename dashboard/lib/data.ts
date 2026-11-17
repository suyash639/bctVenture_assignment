/**
 * Loaders for the static data export. The dashboard reads nothing else.
 * Each loader returns a typed LoadResult and never throws:
 *   ok      — file present and structurally valid
 *   missing — HTTP 404 (the pipeline step that produces it has not run)
 *   error   — any other HTTP failure, unparsable JSON, or a shape that violates the contract
 */
import type { Ad, ClustersFile, DashboardData, Insight, LoadResult, Manifest } from "./types";

export const DATA_BASE = "/data";

export type Fetcher = (input: string) => Promise<Pick<Response, "ok" | "status" | "json">>;

/** Which pipeline step produces each file — shown in empty states. */
export const PRODUCED_BY: Record<string, string> = {
  "manifest.json": "python -m src.export.dashboard_data",
  "ads.json": "python -m src.export.dashboard_data (after the dataset is validated)",
  "clusters.json": "python -m src.pipeline.run (clustering stage), then the exporter",
  "insights.json": "python -m src.pipeline.run (intelligence stage), then the exporter",
};

export async function fetchJson<T>(
  file: string,
  validate: (x: unknown) => string | null,
  fetcher: Fetcher = (u) => fetch(u, { cache: "no-store" }),
): Promise<LoadResult<T>> {
  let res: Awaited<ReturnType<Fetcher>>;
  try {
    res = await fetcher(`${DATA_BASE}/${file}`);
  } catch (e) {
    return { status: "error", data: null, reason: `Could not request ${file}: ${String(e)}` };
  }
  if (res.status === 404) {
    return { status: "missing", data: null, reason: `${file} has not been generated yet. Produced by: ${PRODUCED_BY[file] ?? "the exporter"}.` };
  }
  if (!res.ok) {
    return { status: "error", data: null, reason: `${file}: HTTP ${res.status}` };
  }
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    return { status: "error", data: null, reason: `${file} is not valid JSON` };
  }
  const problem = validate(body);
  if (problem) return { status: "error", data: null, reason: `${file} violates the data contract: ${problem}` };
  return { status: "ok", data: body as T, reason: null };
}

const isObj = (x: unknown): x is Record<string, unknown> => typeof x === "object" && x !== null && !Array.isArray(x);

export function validateManifest(x: unknown): string | null {
  if (!isObj(x)) return "expected an object";
  if (x.schema_version !== "1.0") return `unsupported schema_version ${String(x.schema_version)}`;
  if (typeof x.provisional !== "boolean") return "provisional must be boolean";
  if (!isObj(x.dataset) || typeof x.dataset.n_verified !== "number") return "dataset.n_verified missing";
  if (!isObj(x.available)) return "available missing";
  if (!Array.isArray(x.brands)) return "brands must be an array";
  return null;
}

export function validateAds(x: unknown): string | null {
  if (!Array.isArray(x)) return "expected an array";
  const seen = new Set<string>();
  for (const [i, a] of x.entries()) {
    if (!isObj(a)) return `item ${i} is not an object`;
    if (typeof a.ad_id !== "string") return `item ${i}: ad_id must be a string`;
    if (seen.has(a.ad_id)) return `duplicate ad_id ${a.ad_id}`;
    seen.add(a.ad_id);
    if (typeof a.brand !== "string" || typeof a.image !== "string") return `ad ${a.ad_id}: brand and image are required`;
  }
  return null;
}

export function validateClusters(x: unknown): string | null {
  if (!isObj(x)) return "expected an object";
  if (!Array.isArray(x.clusters)) return "clusters must be an array";
  if (!isObj(x.selected) || !isObj(x.metrics)) return "selected and metrics are required";
  return null;
}

export function validateInsights(x: unknown): string | null {
  if (!Array.isArray(x)) return "expected an array";
  for (const [i, o] of x.entries()) {
    if (!isObj(o) || typeof o.statement !== "string" || !Array.isArray(o.supporting_ad_ids)) {
      return `observation ${i} lacks statement or supporting_ad_ids`;
    }
  }
  return null;
}

export const loadManifest = (f?: Fetcher) => fetchJson<Manifest>("manifest.json", validateManifest, f);
export const loadAds = (f?: Fetcher) => fetchJson<Ad[]>("ads.json", validateAds, f);
export const loadClusters = (f?: Fetcher) => fetchJson<ClustersFile>("clusters.json", validateClusters, f);
export const loadInsights = (f?: Fetcher) => fetchJson<Insight[]>("insights.json", validateInsights, f);

export async function loadAll(f?: Fetcher): Promise<DashboardData> {
  const [manifest, ads, clusters, insights] = await Promise.all([
    loadManifest(f), loadAds(f), loadClusters(f), loadInsights(f),
  ]);
  return { manifest, ads, clusters, insights };
}

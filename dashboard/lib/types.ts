/**
 * Types for dashboard/public/data/*.json — mirrors reports/dashboard_data_contract.md exactly.
 * Every field that can be unavailable is `null`; the UI renders null as "Unavailable".
 */

export interface Manifest {
  schema_version: "1.0";
  generated_at: string;
  provisional: boolean;
  dataset: {
    sha256: string;
    frozen: boolean;
    frozen_at: string | null;
    n_verified: number;
    n_excluded: number;
    per_brand: Record<string, number>;
  };
  pipeline: {
    run_at: string | null;
    feature_variant: string | null;
    clustering_config: string | null;
    clip_model: string | null;
  } | null;
  available: { features: boolean; clusters: boolean; projection: boolean; insights: boolean };
  brands: string[];
}

export type Orientation = "portrait" | "square" | "landscape";
export type TextPosition = "top" | "middle" | "bottom" | "none";

export interface DominantColour {
  hex: string;
  proportion: number;
}

export interface AdFeatures {
  width: number;
  height: number;
  aspect_ratio: number;
  orientation: Orientation;
  brightness: number;
  contrast: number;
  sharpness: number;
  colourfulness: number;
  dominant_colours: DominantColour[];
  colour_distribution: Record<string, number>;
  text_density: number | null;
  text_position: TextPosition | null;
  ocr_text: string | null;
  layout_category: string | null;
  layout_reasons: string[] | null;
}

export interface AdCluster {
  cluster_id: number;
  is_noise: boolean;
  distance_to_centroid: number | null;
}

export interface Ad {
  ad_id: string;
  brand: string;
  advertiser: string;
  advertiser_type: "brand_page" | "sub_brand_page" | "partnership";
  ad_library_url: string;
  status: "Active" | "Inactive" | null;
  start_date: string | null;
  end_date: string | null;
  body: string | null;
  link_caption: string | null;
  link_headline: string | null;
  cta: string | null;
  cta_normalised: string | null;
  landing_url: string | null;
  format: "static" | "carousel" | "video" | null;
  image_type: "static" | "video_thumbnail" | null;
  image: string;
  record_origin: "original" | "replacement";
  replaces_ad_id: string | null;
  features: AdFeatures | null;
  cluster: AdCluster | null;
}

export interface ClusterSummary {
  cluster_id: number;
  is_noise: boolean;
  size: number;
  ad_ids: string[];
  representative_ad_ids: string[];
  brand_mix: Record<string, number>;
  profile: Record<string, unknown>;
}

export interface ClustersFile {
  selected: {
    config_id: string;
    algorithm: string;
    params: Record<string, unknown>;
    rationale: string;
    warnings: string[];
  };
  metrics: {
    silhouette: number | null;
    davies_bouldin: number | null;
    calinski_harabasz: number | null;
    n_clusters: number;
    n_noise: number;
  };
  clusters: ClusterSummary[];
  projection: { ad_id: string; x: number; y: number }[] | null;
}

export interface Insight {
  observation_id: string;
  scope: string;
  statement: string;
  metric: string;
  value: unknown;
  comparison: unknown;
  n: number;
  supporting_ad_ids: string[];
  method: string;
  caveats: string[];
  status: string;
}

export type LoadStatus = "ok" | "missing" | "error";

export interface LoadResult<T> {
  status: LoadStatus;
  data: T | null;
  /** Human-readable explanation when status !== "ok". */
  reason: string | null;
}

export interface DashboardData {
  manifest: LoadResult<Manifest>;
  ads: LoadResult<Ad[]>;
  clusters: LoadResult<ClustersFile>;
  insights: LoadResult<Insight[]>;
}

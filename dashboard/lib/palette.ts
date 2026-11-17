/**
 * Colour tokens. Brands use the Okabe–Ito colour-blind-safe palette in a fixed order so a brand
 * keeps its colour on every chart. Unknown brands fall back to neutral greys (never re-used accents).
 */
export const BRAND_ORDER = ["Kapiva", "OZiva", "Mamaearth", "Himalaya Wellness", "MuscleBlaze"] as const;

const OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#000000"];
const FALLBACK = ["#64748b", "#94a3b8", "#475569", "#cbd5e1"];

export function brandColour(brand: string, brands: readonly string[] = BRAND_ORDER): string {
  const i = brands.indexOf(brand);
  if (i >= 0 && i < OKABE_ITO.length) return OKABE_ITO[i] as string;
  const j = BRAND_ORDER.indexOf(brand as (typeof BRAND_ORDER)[number]);
  if (j >= 0) return OKABE_ITO[j] as string;
  let h = 0;
  for (const c of brand) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return FALLBACK[h % FALLBACK.length] as string;
}

/** Categorical palette for non-brand series (clusters, formats, layouts). */
export const SERIES = ["#4f46e5", "#0891b2", "#ca8a04", "#be185d", "#16a34a", "#9333ea", "#ea580c", "#0f766e", "#64748b"];
export const seriesColour = (i: number): string => SERIES[i % SERIES.length] as string;
export const NOISE_COLOUR = "#94a3b8";

/**
 * Representative swatch for each colour_distribution bucket produced by src/vision/image_features.py
 * (12 hue bins of 30° centred on 0°, 30°, … plus neutral buckets).
 */
export const COLOUR_BUCKETS: { key: string; label: string; hex: string }[] = [
  { key: "white", label: "White", hex: "#f8fafc" },
  { key: "grey", label: "Grey", hex: "#9ca3af" },
  { key: "black", label: "Black", hex: "#111827" },
  { key: "red", label: "Red", hex: "#dc2626" },
  { key: "orange", label: "Orange", hex: "#ea580c" },
  { key: "yellow", label: "Yellow", hex: "#eab308" },
  { key: "yellow_green", label: "Yellow-green", hex: "#84cc16" },
  { key: "green", label: "Green", hex: "#16a34a" },
  { key: "green_cyan", label: "Green-cyan", hex: "#10b981" },
  { key: "cyan", label: "Cyan", hex: "#06b6d4" },
  { key: "azure", label: "Azure", hex: "#0ea5e9" },
  { key: "blue", label: "Blue", hex: "#2563eb" },
  { key: "violet", label: "Violet", hex: "#7c3aed" },
  { key: "magenta", label: "Magenta", hex: "#c026d3" },
  { key: "rose", label: "Rose", hex: "#e11d48" },
];

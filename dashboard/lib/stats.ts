/**
 * Pure helpers for simple descriptive statistics derived from ads.json.
 * The contract allows only counts/percentages/quantiles computed from exported values —
 * every helper returns n so the UI can label it.
 */
import type { Ad } from "./types";

export function countBy<T>(items: T[], key: (t: T) => string | null | undefined): { key: string; count: number }[] {
  const m = new Map<string, number>();
  for (const it of items) {
    const k = key(it) ?? "Unavailable";
    m.set(k, (m.get(k) ?? 0) + 1);
  }
  return [...m.entries()].map(([k, count]) => ({ key: k, count })).sort((a, b) => b.count - a.count || a.key.localeCompare(b.key));
}

export interface Quantiles {
  n: number;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
}

/** Linear-interpolation quantiles (same convention as numpy's default). null when n = 0. */
export function quantiles(values: number[]): Quantiles | null {
  const v = values.filter((x) => Number.isFinite(x)).sort((a, b) => a - b);
  if (v.length === 0) return null;
  const q = (p: number) => {
    const pos = (v.length - 1) * p;
    const lo = Math.floor(pos);
    const hi = Math.ceil(pos);
    const a = v[lo] as number;
    const b = v[hi] as number;
    return a + (b - a) * (pos - lo);
  };
  return { n: v.length, min: v[0] as number, q1: q(0.25), median: q(0.5), q3: q(0.75), max: v[v.length - 1] as number };
}

/** Mean colour_distribution over the ads that have features; n = ads included. */
export function meanColourDistribution(ads: Ad[]): { n: number; shares: Record<string, number> } {
  const withF = ads.filter((a) => a.features?.colour_distribution);
  const shares: Record<string, number> = {};
  for (const a of withF) {
    for (const [k, v] of Object.entries(a.features!.colour_distribution)) shares[k] = (shares[k] ?? 0) + v;
  }
  for (const k of Object.keys(shares)) shares[k] = (shares[k] as number) / withF.length;
  return { n: withF.length, shares };
}

export const pct = (part: number, whole: number): string => (whole > 0 ? `${((100 * part) / whole).toFixed(0)}%` : "—");

export const fmt = (x: number | null | undefined, digits = 2): string =>
  x === null || x === undefined || !Number.isFinite(x) ? "Unavailable" : x.toFixed(digits);

/** Deterministic jitter in [-0.5, 0.5) from a string (for strip plots — no randomness). */
export function stableJitter(id: string): number {
  let h = 2166136261;
  for (let i = 0; i < id.length; i++) {
    h ^= id.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 1000) / 1000 - 0.5;
}

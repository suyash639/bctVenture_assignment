/** Filter and stats logic, on SYNTHETIC fixtures only. */
import { describe, expect, it } from "vitest";
import { EMPTY_FILTER, filterAds } from "@/lib/filters";
import { countBy, meanColourDistribution, quantiles, stableJitter } from "@/lib/stats";
import { brandColour } from "@/lib/palette";
import type { Ad } from "@/lib/types";
import raw from "./fixtures/synthetic_ads.json";

const ads = raw as unknown as Ad[];
const ids = (xs: Ad[]) => xs.map((a) => a.ad_id);

describe("SYNTHETIC: filters", () => {
  it("empty filter keeps everything", () => {
    expect(ids(filterAds(ads, EMPTY_FILTER))).toEqual(["SYNTH-0001", "SYNTH-0002", "SYNTH-0003"]);
  });
  it("searches ad_id, copy and OCR text case-insensitively", () => {
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, query: "synth-0003" }))).toEqual(["SYNTH-0003"]);
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, query: "ALPHA" }))).toEqual(["SYNTH-0001"]);
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, query: "ocr beta" }))).toEqual(["SYNTH-0001"]);
  });
  it("filters by brand, format and layout (including unavailable)", () => {
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, brand: "SyntheticBrandA" }))).toEqual(["SYNTH-0001", "SYNTH-0003"]);
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, format: "carousel" }))).toEqual(["SYNTH-0002"]);
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, layout: "unavailable" }))).toEqual(["SYNTH-0002", "SYNTH-0003"]);
  });
  it("cluster filter separates clusters, noise and unassigned", () => {
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, cluster: "0" }))).toEqual(["SYNTH-0001"]);
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, cluster: "noise" }))).toEqual(["SYNTH-0002"]);
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, cluster: "unassigned" }))).toEqual(["SYNTH-0003"]);
    // a noise point is never matched as cluster "-1"
    expect(ids(filterAds(ads, { ...EMPTY_FILTER, cluster: "-1" }))).toEqual([]);
  });
});

describe("SYNTHETIC: stats", () => {
  it("countBy labels nulls as Unavailable", () => {
    expect(countBy(ads, (a) => a.status)).toEqual([
      { key: "Active", count: 1 }, { key: "Inactive", count: 1 }, { key: "Unavailable", count: 1 },
    ]);
  });
  it("quantiles match linear interpolation and handle empty input", () => {
    expect(quantiles([4, 1, 3, 2])).toEqual({ n: 4, min: 1, q1: 1.75, median: 2.5, q3: 3.25, max: 4 });
    expect(quantiles([])).toBeNull();
  });
  it("mean colour distribution only uses ads with features and reports n", () => {
    const r = meanColourDistribution(ads);
    expect(r.n).toBe(1);
    expect(r.shares).toEqual({ white: 0.4, blue: 0.6 });
  });
  it("jitter is deterministic and bounded", () => {
    expect(stableJitter("SYNTH-0001")).toBe(stableJitter("SYNTH-0001"));
    expect(Math.abs(stableJitter("x"))).toBeLessThanOrEqual(0.5);
  });
  it("brand colours are fixed per brand", () => {
    expect(brandColour("Kapiva")).toBe(brandColour("Kapiva"));
    expect(brandColour("Kapiva")).not.toBe(brandColour("OZiva"));
  });
});

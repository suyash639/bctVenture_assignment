/**
 * Contract test: runs the dashboard's own validators against a REAL export produced by
 * `python -m src.export.dashboard_data`. Skipped unless EXPORT_DIR points at one, e.g.
 *   EXPORT_DIR=/abs/path/to/export npx vitest run tests/export_contract.test.ts
 * (tests/test_export.py in the Python suite does this automatically).
 */
import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { validateAds, validateClusters, validateInsights, validateManifest } from "@/lib/data";

const dir = process.env.EXPORT_DIR;
const read = (f: string) => JSON.parse(fs.readFileSync(path.join(dir as string, f), "utf8"));

describe.skipIf(!dir)("export matches the dashboard data contract", () => {
  it("manifest.json", () => expect(validateManifest(read("manifest.json"))).toBeNull());
  it("ads.json", () => {
    const ads = read("ads.json");
    expect(validateAds(ads)).toBeNull();
    for (const a of ads) expect(fs.existsSync(path.join(dir as string, a.image.replace(/^\/data\//, "")))).toBe(true);
  });
  it("clusters.json (if present)", () => {
    if (fs.existsSync(path.join(dir as string, "clusters.json"))) expect(validateClusters(read("clusters.json"))).toBeNull();
  });
  it("insights.json (if present)", () => {
    if (fs.existsSync(path.join(dir as string, "insights.json"))) expect(validateInsights(read("insights.json"))).toBeNull();
  });
});

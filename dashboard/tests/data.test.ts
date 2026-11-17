/**
 * Loader tests. All payloads are SYNTHETIC fixtures (tests/fixtures/synthetic_*.json) or inline
 * synthetic objects — never real data and never served by the app.
 */
import { describe, expect, it } from "vitest";
import { fetchJson, loadAds, loadAll, loadManifest, validateAds, validateInsights } from "@/lib/data";
import type { Fetcher } from "@/lib/data";
import syntheticAds from "./fixtures/synthetic_ads.json";
import syntheticManifest from "./fixtures/synthetic_manifest.json";

const respond = (status: number, body?: unknown, badJson = false): ReturnType<Fetcher> =>
  Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => (badJson ? Promise.reject(new SyntaxError("bad json")) : Promise.resolve(body)),
  });

const fetcherFor = (files: Record<string, unknown>): Fetcher => (url) => {
  const name = url.replace("/data/", "");
  return name in files ? respond(200, files[name]) : respond(404);
};

describe("SYNTHETIC: data loaders", () => {
  it("returns ok with typed data when the file exists and is valid", async () => {
    const r = await loadAds(fetcherFor({ "ads.json": syntheticAds }));
    expect(r.status).toBe("ok");
    expect(r.data?.map((a) => a.ad_id)).toEqual(["SYNTH-0001", "SYNTH-0002", "SYNTH-0003"]);
    expect(r.reason).toBeNull();
  });

  it("returns missing (not error) on 404, naming the producing pipeline step", async () => {
    const r = await loadManifest(fetcherFor({}));
    expect(r.status).toBe("missing");
    expect(r.data).toBeNull();
    expect(r.reason).toMatch(/manifest\.json/);
    expect(r.reason).toMatch(/src\.export\.dashboard_data/);
  });

  it("returns error on HTTP failure, bad JSON, network failure and contract violations", async () => {
    expect((await fetchJson("ads.json", validateAds, () => respond(500))).status).toBe("error");
    expect((await fetchJson("ads.json", validateAds, () => respond(200, null, true))).status).toBe("error");
    expect((await fetchJson("ads.json", validateAds, () => Promise.reject(new Error("offline")))).status).toBe("error");
    const dup = await loadAds(fetcherFor({ "ads.json": [syntheticAds[0], syntheticAds[0]] }));
    expect(dup.status).toBe("error");
    expect(dup.reason).toMatch(/duplicate ad_id/);
    const wrongSchema = await loadManifest(fetcherFor({ "manifest.json": { ...syntheticManifest, schema_version: "9" } }));
    expect(wrongSchema.status).toBe("error");
  });

  it("loadAll reports each file independently", async () => {
    const all = await loadAll(fetcherFor({ "manifest.json": syntheticManifest, "ads.json": syntheticAds }));
    expect(all.manifest.status).toBe("ok");
    expect(all.ads.status).toBe("ok");
    expect(all.clusters.status).toBe("missing");
    expect(all.insights.status).toBe("missing");
  });

  it("insight validation requires supporting_ad_ids (traceability)", () => {
    expect(validateInsights([{ statement: "x" }])).toMatch(/supporting_ad_ids/);
    expect(validateInsights([{ statement: "x", supporting_ad_ids: ["SYNTH-0001"] }])).toBeNull();
  });
});

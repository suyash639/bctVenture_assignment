"use client";

import type { AdFilter } from "@/lib/filters";
import { EMPTY_FILTER } from "@/lib/filters";

interface Options {
  brands: string[];
  formats: string[];
  layouts: string[];
  clusters: string[]; // already-stringified cluster ids, plus "noise"/"unassigned" when present
}

function Select({ id, label, value, onChange, options }: {
  id: string; label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[];
}) {
  return (
    <label htmlFor={id} className="flex flex-col gap-1 text-xs font-medium text-slate-600">
      {label}
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-800 focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500"
      >
        <option value="all">All</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function FilterBar({ value, onChange, options, resultCount, total }: {
  value: AdFilter; onChange: (f: AdFilter) => void; options: Options; resultCount: number; total: number;
}) {
  const set = (patch: Partial<AdFilter>) => onChange({ ...value, ...patch });
  const pretty = (s: string) => s.replace(/_/g, " ");
  return (
    <form role="search" onSubmit={(e) => e.preventDefault()} className="mb-4 rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
        <label htmlFor="f-query" className="col-span-2 flex flex-col gap-1 text-xs font-medium text-slate-600">
          Search
          <input
            id="f-query"
            type="search"
            value={value.query}
            onChange={(e) => set({ query: e.target.value })}
            placeholder="Ad ID, brand, copy or on-image text"
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-800 focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500"
          />
        </label>
        <Select id="f-brand" label="Brand" value={value.brand} onChange={(v) => set({ brand: v })} options={options.brands.map((b) => ({ value: b, label: b }))} />
        <Select id="f-format" label="Format" value={value.format} onChange={(v) => set({ format: v })} options={options.formats.map((b) => ({ value: b, label: b }))} />
        <Select id="f-layout" label="Layout" value={value.layout} onChange={(v) => set({ layout: v })} options={options.layouts.map((b) => ({ value: b, label: pretty(b) }))} />
        <Select
          id="f-cluster"
          label="Cluster"
          value={value.cluster}
          onChange={(v) => set({ cluster: v })}
          options={options.clusters.map((c) => ({ value: c, label: c === "noise" || c === "unassigned" ? pretty(c) : `Cluster ${c}` }))}
        />
      </div>
      <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
        <span aria-live="polite">
          Showing {resultCount} of {total} verified ads
        </span>
        <button type="button" onClick={() => onChange(EMPTY_FILTER)} className="rounded px-2 py-1 text-accent-600 hover:bg-accent-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500">
          Reset filters
        </button>
      </div>
    </form>
  );
}

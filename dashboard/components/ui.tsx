/**
 * Small reusable presentational components. No component here computes or invents data:
 * values are passed in, and null/undefined always render as <UnavailableValue/>.
 */
import { useState, type ReactNode } from "react";
import { brandColour } from "@/lib/palette";
import { ExplanationBox } from "./Explanation";
import type { PillarExplanation } from "@/lib/explanations";

export function UnavailableValue({ reason }: { reason?: string }) {
  return (
    <span
      className="inline-flex items-center rounded border border-dashed border-slate-300 bg-slate-50 px-1.5 py-0.5 text-xs font-medium text-slate-500"
      title={reason ?? "Not available in the exported data"}
    >
      Unavailable
    </span>
  );
}

/** Renders a value, or "Unavailable" for null/undefined/empty string. */
export function Value({ v, children }: { v: unknown; children?: ReactNode }) {
  if (v === null || v === undefined || v === "") return <UnavailableValue />;
  return <>{children ?? String(v)}</>;
}

export function StatCard({
  label,
  value,
  hint,
  explanation,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  explanation?: PillarExplanation;
}) {
  const [showExplanation, setShowExplanation] = useState(false);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-all">
      <div className="flex items-start justify-between gap-2">
        <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
        {explanation ? (
          <button
            type="button"
            onClick={() => setShowExplanation((prev) => !prev)}
            className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 ${
              showExplanation
                ? "bg-accent-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
            }`}
            title={`Explain ${label}`}
            aria-expanded={showExplanation}
          >
            <span>ℹ️</span>
            <span>{showExplanation ? "Hide" : "Explain"}</span>
          </button>
        ) : null}
      </div>
      <dd className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{value}</dd>
      {hint ? <dd className="mt-1 text-xs text-slate-500">{hint}</dd> : null}

      {explanation && showExplanation ? (
        <div className="mt-3 border-t border-slate-100 pt-3">
          <ExplanationBox explanation={explanation} defaultOpen={true} title={`Understanding ${label}`} />
        </div>
      ) : null}
    </div>
  );
}

export function ChartCard({
  title,
  subtitle,
  children,
  footer,
  id,
  explanation,
  explanationTitle,
}: {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  id?: string;
  explanation?: PillarExplanation;
  explanationTitle?: string;
}) {
  const headingId = id ? `${id}-title` : undefined;
  return (
    <section aria-labelledby={headingId} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <header className="mb-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 id={headingId} className="text-sm font-semibold text-slate-900">
              {title}
            </h2>
            {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
          </div>
        </div>
      </header>
      {children}
      {explanation ? (
        <div className="mt-3 border-t border-slate-100 pt-3">
          <ExplanationBox explanation={explanation} title={explanationTitle ?? `Guide: How to read ${title}`} />
        </div>
      ) : null}
      {footer ? <footer className="mt-3 border-t border-slate-100 pt-2 text-xs text-slate-500">{footer}</footer> : null}
    </section>
  );
}

export function BrandBadge({ brand }: { brand: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-700">
      <span aria-hidden className="h-2 w-2 rounded-full" style={{ backgroundColor: brandColour(brand) }} />
      {brand}
    </span>
  );
}

export function Tag({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "accent" | "warn" }) {
  const cls =
    tone === "accent"
      ? "bg-accent-50 text-accent-700 border-accent-100"
      : tone === "warn"
        ? "bg-amber-50 text-amber-800 border-amber-200"
        : "bg-slate-50 text-slate-700 border-slate-200";
  return <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-medium ${cls}`}>{children}</span>;
}

export function EmptyState({ title, reason, action }: { title: string; reason?: string | null; action?: ReactNode }) {
  return (
    <div role="status" className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
      <svg aria-hidden className="h-8 w-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h12A2.25 2.25 0 0120.25 6v12A2.25 2.25 0 0118 20.25H6A2.25 2.25 0 013.75 18V6zM3.75 15l4.5-4.5 3 3 3-3 6 6" />
      </svg>
      <p className="mt-3 text-sm font-semibold text-slate-800">{title}</p>
      {reason ? <p className="mt-1 max-w-md text-sm text-slate-500">{reason}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function LoadingState({ label = "Loading data…" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="space-y-3">
      <span className="sr-only">{label}</span>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-200/70" />
        ))}
      </div>
      <div className="h-64 animate-pulse rounded-lg bg-slate-200/70" />
    </div>
  );
}

export function ProvisionalBanner() {
  return (
    <div role="alert" className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
      <strong className="font-semibold">Provisional data</strong> — dataset not frozen; not for citation.
    </div>
  );
}

export function PageHeader({ title, description, children }: { title: string; description?: ReactNode; children?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        {description ? <p className="mt-1 max-w-3xl text-sm text-slate-500">{description}</p> : null}
      </div>
      {children}
    </div>
  );
}

/** Accessible fallback table under a chart (the "view data" toggle). */
export function DataTable({ caption, headers, rows }: { caption: string; headers: string[]; rows: ReactNode[][] }) {
  return (
    <details className="mt-3 text-xs">
      <summary className="cursor-pointer select-none text-slate-500 hover:text-slate-700">View data ({rows.length} rows)</summary>
      <div className="mt-2 max-h-72 overflow-auto">
        <table className="w-full border-collapse text-left">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {headers.map((h) => (
                <th key={h} scope="col" className="border-b border-slate-200 px-2 py-1 font-medium text-slate-600">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="odd:bg-slate-50">
                {r.map((c, j) => (
                  <td key={j} className="px-2 py-1 tabular-nums text-slate-700">
                    {c}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

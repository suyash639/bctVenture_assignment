"use client";

import { useState, type ReactNode } from "react";
import type { PillarExplanation } from "@/lib/explanations";

export interface ExplanationBoxProps {
  explanation: PillarExplanation;
  title?: string;
  defaultOpen?: boolean;
  compact?: boolean;
  className?: string;
}

/**
 * Reusable 6-Pillar Educational Explanation Component
 * Transforms charts, metrics, and clusters into self-explanatory intelligence.
 */
export function ExplanationBox({
  explanation,
  title = "How to read & interpret this",
  defaultOpen = false,
  compact = false,
  className = "",
}: ExplanationBoxProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={`rounded-md border border-slate-200 bg-slate-50/75 transition-colors ${className}`}>
      <button
        type="button"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium text-slate-700 hover:bg-slate-100/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 rounded-md"
      >
        <span className="flex items-center gap-1.5 text-accent-700 font-semibold">
          <svg className="h-4 w-4 shrink-0 text-accent-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{title}</span>
          {!isOpen && explanation.whyItMatters ? (
            <span className="hidden text-slate-500 font-normal sm:inline">
              — <span className="line-clamp-1 italic">{explanation.whyItMatters.slice(0, 75)}…</span>
            </span>
          ) : null}
        </span>
        <span className="flex items-center gap-1 text-[11px] font-medium text-accent-700">
          <span>{isOpen ? "Hide guide" : "Explain"}</span>
          <svg
            className={`h-3.5 w-3.5 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      {isOpen ? (
        <div className="border-t border-slate-200 p-3.5 text-xs text-slate-800 space-y-3 animate-fadeIn">
          {/* 1. What am I looking at? */}
          <div className="flex gap-2.5 items-start">
            <span className="inline-flex items-center justify-center rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-bold text-blue-800 shrink-0 uppercase tracking-wider">
              1. What
            </span>
            <div className="min-w-0">
              <p className="font-semibold text-slate-900">What am I looking at?</p>
              <p className="mt-0.5 text-slate-600 leading-relaxed">{explanation.what}</p>
            </div>
          </div>

          {/* 2. How is it calculated? */}
          {explanation.calculation ? (
            <div className="flex gap-2.5 items-start">
              <span className="inline-flex items-center justify-center rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold text-purple-800 shrink-0 uppercase tracking-wider">
                2. Logic
              </span>
              <div className="min-w-0">
                <p className="font-semibold text-slate-900">How is it calculated?</p>
                <p className="mt-0.5 text-slate-600 leading-relaxed font-mono text-[11px] bg-white p-1.5 rounded border border-slate-200">
                  {explanation.calculation}
                </p>
              </div>
            </div>
          ) : null}

          {/* 3. Why does it matter? */}
          <div className="flex gap-2.5 items-start">
            <span className="inline-flex items-center justify-center rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-800 shrink-0 uppercase tracking-wider">
              3. Why
            </span>
            <div className="min-w-0">
              <p className="font-semibold text-slate-900">Why does it matter?</p>
              <p className="mt-0.5 text-slate-600 leading-relaxed">{explanation.whyItMatters}</p>
            </div>
          </div>

          {/* 4. What our data shows (Dynamic observation) */}
          {explanation.whatItTellsUs ? (
            <div className="flex gap-2.5 items-start bg-accent-50/60 p-2 rounded-md border border-accent-100">
              <span className="inline-flex items-center justify-center rounded bg-accent-200 px-1.5 py-0.5 text-[10px] font-bold text-accent-900 shrink-0 uppercase tracking-wider">
                4. Data
              </span>
              <div className="min-w-0">
                <p className="font-semibold text-accent-950">What our data shows</p>
                <p className="mt-0.5 text-accent-900 leading-relaxed">{explanation.whatItTellsUs}</p>
              </div>
            </div>
          ) : null}

          {/* 5. Business Value */}
          {explanation.businessValue ? (
            <div className="flex gap-2.5 items-start">
              <span className="inline-flex items-center justify-center rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-800 shrink-0 uppercase tracking-wider">
                5. Action
              </span>
              <div className="min-w-0">
                <p className="font-semibold text-slate-900">Business value & decision support</p>
                <p className="mt-0.5 text-slate-600 leading-relaxed">{explanation.businessValue}</p>
              </div>
            </div>
          ) : null}

          {/* 6. Limitations */}
          {explanation.limitations ? (
            <div className="flex gap-2.5 items-start bg-rose-50/50 p-2 rounded-md border border-rose-100">
              <span className="inline-flex items-center justify-center rounded bg-rose-100 px-1.5 py-0.5 text-[10px] font-bold text-rose-800 shrink-0 uppercase tracking-wider">
                6. Caution
              </span>
              <div className="min-w-0">
                <p className="font-semibold text-rose-950">Limitations & analytical boundaries</p>
                <p className="mt-0.5 text-rose-800 leading-relaxed">{explanation.limitations}</p>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/**
 * Interactive Info Pill Trigger
 * Placed neatly next to a KPI or header.
 */
export function InfoPill({
  label = "Explain",
  onClick,
  active = false,
}: {
  label?: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 ${
        active
          ? "bg-accent-600 text-white shadow-xs"
          : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
      }`}
      aria-label={`${label} explanation`}
    >
      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{label}</span>
    </button>
  );
}

/**
 * Educational Callout with beginner & expert tabs
 */
export function ConceptExplainer({
  concept,
  beginner,
  technical,
  businessValue,
  limitations,
}: {
  concept: string;
  beginner: string;
  technical?: string;
  businessValue?: string;
  limitations?: string;
}) {
  const [tab, setTab] = useState<"beginner" | "technical">("beginner");

  return (
    <div className="rounded-lg border border-accent-200 bg-white p-4 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-100 text-accent-700 text-xs font-bold">
            💡
          </span>
          <h3 className="text-sm font-semibold text-slate-900">{concept}</h3>
        </div>
        <div className="flex rounded-md bg-slate-100 p-0.5 text-xs font-medium text-slate-600">
          <button
            type="button"
            onClick={() => setTab("beginner")}
            className={`rounded px-2 py-0.5 transition-colors ${
              tab === "beginner" ? "bg-white font-semibold text-accent-700 shadow-xs" : "hover:text-slate-900"
            }`}
          >
            Explain like I&apos;m a beginner
          </button>
          {technical ? (
            <button
              type="button"
              onClick={() => setTab("technical")}
              className={`rounded px-2 py-0.5 transition-colors ${
                tab === "technical" ? "bg-white font-semibold text-accent-700 shadow-xs" : "hover:text-slate-900"
              }`}
            >
              Technical details
            </button>
          ) : null}
        </div>
      </div>

      <div className="mt-3 text-xs leading-relaxed text-slate-700 space-y-2">
        {tab === "beginner" ? (
          <p className="bg-amber-50/60 p-2.5 rounded border border-amber-100 text-slate-800">
            {beginner}
          </p>
        ) : (
          <div className="space-y-1.5 font-mono text-[11px] bg-slate-50 p-2.5 rounded border border-slate-200 text-slate-800">
            {technical}
          </div>
        )}

        {businessValue ? (
          <p className="text-slate-600">
            <strong className="text-slate-900">Marketer&apos;s takeaway:</strong> {businessValue}
          </p>
        ) : null}

        {limitations ? (
          <p className="text-rose-700 text-[11px]">
            <strong>Caution:</strong> {limitations}
          </p>
        ) : null}
      </div>
    </div>
  );
}


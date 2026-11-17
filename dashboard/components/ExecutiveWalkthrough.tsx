"use client";

import { useState } from "react";

export interface WalkthroughStep {
  step: number;
  title: string;
  summary: string;
  detail: string;
  whyItMatters: string;
  caution: string;
}

export const PIPELINE_STEPS: WalkthroughStep[] = [
  {
    step: 1,
    title: "1. Public Ad Discovery & Access",
    summary: "Collecting public active and inactive advertisements from Meta Ad Library.",
    detail:
      "Using permitted, public browser automation without bypassing credentials, login, or platform barriers. Target ads are collected across 5 Indian wellness brands with full metadata (headline, primary text, CTA, landing URL, dates).",
    whyItMatters:
      "Provides objective, unvarnished insight into what competitors are publishing in the live advertising auction right now.",
    caution:
      "Public ad libraries show what was published, but never disclose ad spend, audience targeting, or return on investment.",
  },
  {
    step: 2,
    title: "2. Forensic Verification & Asset Auditing",
    summary: "Quarantining low-res thumbnails, duplicates, and unverified partner listings.",
    detail:
      "Every candidate ad card is checked for official advertiser domain matching, live card URL validity, and full-resolution creative assets (PNG format, >=600px shorter side). Replaced low-res video player thumbnails with genuine static ads from the same brand.",
    whyItMatters:
      "Garbage in = garbage out. Corrupt thumbnails or cropped reel frames ruin computer vision algorithms and lead to false business conclusions.",
    caution:
      "Excluding video ads was done solely for static image clustering fidelity; it does not mean video ads are ineffective for advertisers.",
  },
  {
    step: 3,
    title: "3. Pixel & Text Feature Extraction",
    summary: "Extracting color histograms, brightness, contrast, sharpness, and OCR text.",
    detail:
      "Directly from image pixels: K-means color clustering extracts dominant palettes in HSV space; Laplacian variance computes sharpness; Hasler-Süsstrunk measures colorfulness; Optical Character Recognition (OCR) measures on-image text area density.",
    whyItMatters:
      "Quantifies subjective design attributes into hard empirical numbers that can be benchmarked objectively across competitors.",
    caution:
      "Measures visual composition only. A high-contrast ad is not inherently 'better' than a soft-focus ad; both serve different brand objectives.",
  },
  {
    step: 4,
    title: "4. Neural Vision-Language Embeddings",
    summary: "Converting visual images into 512-dimensional semantic representations via OpenCLIP.",
    detail:
      "Each ad creative passes through a pretrained OpenCLIP ViT-B/32 vision transformer. The neural network produces a 512-dimensional vector that captures high-level visual concepts, layout arrangement, subject matter, and emotional tone.",
    whyItMatters:
      "Allows computers to understand visual similarity the way humans do—recognizing that two different bottles on a white background are visually related.",
    caution:
      "Embeddings capture visual and semantic concepts; they have no concept of advertising effectiveness or sales conversion.",
  },
  {
    step: 5,
    title: "5. Unsupervised Visual Clustering",
    summary: "Grouping visually and conceptually similar creatives without human bias.",
    detail:
      "Hierarchical Agglomerative clustering with cosine distance groups creatives into 8 distinct visual archetypes. 24 hyperparameter configurations were evaluated using Silhouette, Davies–Bouldin, and Calinski–Harabasz metrics to guarantee mathematical stability.",
    whyItMatters:
      "Reveals the underlying visual playbooks used in performance marketing across competitors (e.g., product packshots vs dark athletic contrast).",
    caution:
      "Clusters reflect mathematical similarity in vector space. A cluster does not equal an audience segment or campaign goal.",
  },
  {
    step: 6,
    title: "6. Cross-Brand Distribution Benchmarking",
    summary: "Comparing creative styles, formats, CTAs, colors, and layouts across competitors.",
    detail:
      "Normalizing metrics across all 5 brands to compare proportions: layout category shares, color palette dominance, on-image typography density quantiles, and call-to-action choices.",
    whyItMatters:
      "Answers critical strategic questions: Where are competitors copying each other? Where is the category visually saturated? Where is the open white-space?",
    caution:
      "Comparing creative frequency is not market share. A brand running 10 ads might be outspending a brand running 50 ads.",
  },
  {
    step: 7,
    title: "7. Evidence-Backed Decision Support",
    summary: "Generating strategic takeaways with explicit confidence ratings and caveats.",
    detail:
      "Every observation provides exact supporting ad IDs, mathematical baselines, business implications, confidence ratings, and strict limitations. Prohibits unsupported claims about 'winning' ads or conversion rates.",
    whyItMatters:
      "Translates complex machine learning outputs into actionable creative testing roadmaps for designers, copywriters, and CMOs.",
    caution:
      "Never treat creative intelligence as a guarantee of ROAS. Creative insights must be validated through your own controlled in-market split tests.",
  },
];

export function ExecutiveWalkthrough({
  defaultExpanded = false,
  className = "",
}: {
  defaultExpanded?: boolean;
  className?: string;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [activeStep, setActiveStep] = useState<number>(1);

  const current = PIPELINE_STEPS.find((s) => s.step === activeStep) ?? PIPELINE_STEPS[0];

  return (
    <section
      aria-label="How to read this dashboard"
      className={`rounded-xl border border-accent-200 bg-gradient-to-br from-white via-accent-50/20 to-slate-50 p-5 shadow-sm ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-600 text-white font-bold shadow-xs">
            🧭
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              How to Read This Dashboard — Executive Walkthrough
            </h2>
            <p className="text-xs text-slate-600">
              A beginner-friendly guide to our 7-step analytical journey from raw ad pixels to strategic decision support.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-accent-300 bg-white px-3 py-1.5 text-xs font-semibold text-accent-700 shadow-2xs hover:bg-accent-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 transition-colors"
        >
          <span>{expanded ? "Collapse walkthrough" : "Open 7-step walkthrough"}</span>
          <svg
            className={`h-4 w-4 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {expanded ? (
        <div className="mt-5 border-t border-slate-200/80 pt-5 animate-fadeIn">
          {/* Horizontal Step Navigation */}
          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4 lg:grid-cols-7 mb-4">
            {PIPELINE_STEPS.map((s) => {
              const isActive = s.step === activeStep;
              return (
                <button
                  key={s.step}
                  type="button"
                  onClick={() => setActiveStep(s.step)}
                  className={`flex flex-col items-start rounded-md border p-2 text-left text-xs transition-all ${
                    isActive
                      ? "border-accent-600 bg-accent-600 text-white shadow-xs font-semibold"
                      : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <span className={`text-[10px] font-bold ${isActive ? "text-accent-100" : "text-accent-700"}`}>
                    Step 0{s.step}
                  </span>
                  <span className="line-clamp-1 mt-0.5 text-[11px]">{s.title.slice(3)}</span>
                </button>
              );
            })}
          </div>

          {/* Active Step Detailed Card */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-2xs">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2">
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-accent-700">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent-100 text-[11px]">
                  {current.step}
                </span>
                {current.title}
              </span>
              <span className="text-xs text-slate-500 font-medium">
                Step {current.step} of 7 in data pipeline
              </span>
            </div>

            <p className="mt-3 text-sm font-semibold text-slate-900">{current.summary}</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-600">{current.detail}</p>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-md border border-emerald-100 bg-emerald-50/60 p-2.5">
                <p className="text-xs font-bold text-emerald-900 flex items-center gap-1">
                  <span>💡</span> Why it matters
                </p>
                <p className="mt-0.5 text-xs text-emerald-800 leading-relaxed">{current.whyItMatters}</p>
              </div>

              <div className="rounded-md border border-rose-100 bg-rose-50/60 p-2.5">
                <p className="text-xs font-bold text-rose-900 flex items-center gap-1">
                  <span>⚠️</span> Important limitation
                </p>
                <p className="mt-0.5 text-xs text-rose-800 leading-relaxed">{current.caution}</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}


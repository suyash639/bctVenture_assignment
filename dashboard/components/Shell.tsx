"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { useDashboardData } from "./DataProvider";
import { ProvisionalBanner } from "./ui";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/brands/", label: "Brand Comparison" },
  { href: "/creatives/", label: "Creatives" },
  { href: "/clusters/", label: "Cluster Explorer" },
  { href: "/insights/", label: "Insights" },
];

function isActive(path: string, href: string) {
  const norm = (s: string) => (s.endsWith("/") ? s : `${s}/`);
  return href === "/" ? norm(path) === "/" : norm(path).startsWith(href);
}

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname() ?? "/";
  const [open, setOpen] = useState(false);
  const { data } = useDashboardData();
  const manifest = data?.manifest.data;

  const nav = (
    <nav aria-label="Main" className="flex flex-col gap-1">
      {NAV.map((n) => {
        const active = isActive(path, n.href);
        return (
          <Link
            key={n.href}
            href={n.href}
            aria-current={active ? "page" : undefined}
            onClick={() => setOpen(false)}
            className={`rounded-md px-3 py-2 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 ${
              active ? "bg-accent-50 text-accent-700" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            {n.label}
          </Link>
        );
      })}
    </nav>
  );

  const footer = (
    <div className="mt-auto space-y-1 border-t border-slate-200 pt-3 text-xs text-slate-500">
      {manifest ? (
        <>
          <p>
            Data exported <time dateTime={manifest.generated_at}>{manifest.generated_at.slice(0, 16).replace("T", " ")}</time>
          </p>
          <p title={manifest.dataset.sha256}>Dataset {manifest.dataset.sha256.slice(0, 10)}…{manifest.dataset.frozen ? " · frozen" : " · not frozen"}</p>
        </>
      ) : (
        <p>No data export loaded</p>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:shadow">
        Skip to content
      </a>
      {manifest?.provisional ? <ProvisionalBanner /> : null}
      <div className="flex">
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col gap-6 border-r border-slate-200 bg-white p-4 md:flex">
          <Brandmark />
          {nav}
          {footer}
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
            <Brandmark />
            <button
              type="button"
              aria-expanded={open}
              aria-controls="mobile-nav"
              onClick={() => setOpen((o) => !o)}
              className="rounded-md border border-slate-300 px-2.5 py-1 text-sm text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500"
            >
              Menu
            </button>
          </header>
          {open ? (
            <div id="mobile-nav" className="border-b border-slate-200 bg-white p-3 md:hidden">
              {nav}
            </div>
          ) : null}
          <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}

function Brandmark() {
  return (
    <Link href="/" className="flex items-center gap-2 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500">
      <span aria-hidden className="grid h-7 w-7 place-items-center rounded-md bg-accent-600 text-xs font-bold text-white">
        MA
      </span>
      <span className="text-sm font-semibold leading-tight text-slate-900">
        Meta Ads
        <br />
        <span className="font-normal text-slate-500">Creative Intelligence</span>
      </span>
    </Link>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import type { Ad } from "@/lib/types";
import { BrandBadge, Tag } from "./ui";

/** Thumbnail of a real exported creative. If the image fails to load we say so — never a stand-in image. */
export function CreativeImage({ ad, className = "" }: { ad: Ad; className?: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div className={`flex items-center justify-center bg-slate-100 text-xs text-slate-500 ${className}`} role="img" aria-label={`Image unavailable for ad ${ad.ad_id}`}>
        Image unavailable
      </div>
    );
  }
  return (
    <img
      src={ad.image}
      alt={`${ad.brand} creative, Ad Library ID ${ad.ad_id}`}
      loading="lazy"
      onError={() => setFailed(true)}
      className={`bg-slate-50 object-contain ${className}`}
    />
  );
}

export function CreativeCard({ ad, highlight = false }: { ad: Ad; highlight?: boolean }) {
  return (
    <Link
      href={`/creative/?id=${encodeURIComponent(ad.ad_id)}`}
      className={`group flex flex-col overflow-hidden rounded-lg border bg-white shadow-sm transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 ${
        highlight ? "border-accent-500 ring-1 ring-accent-500" : "border-slate-200"
      }`}
    >
      <CreativeImage ad={ad} className="aspect-square w-full" />
      <div className="flex flex-col gap-1.5 p-2.5">
        <div className="flex flex-wrap items-center justify-between gap-1.5">
          <BrandBadge brand={ad.brand} />
          {highlight ? <span className="shrink-0 whitespace-nowrap"><Tag tone="accent">Representative</Tag></span> : null}
        </div>
        <p className="truncate font-mono text-xs text-slate-500" title={ad.ad_id}>
          {ad.ad_id}
        </p>
        <div className="flex flex-wrap gap-1">
          {ad.format ? <Tag>{ad.format}</Tag> : null}
          {ad.features?.layout_category ? <Tag>{ad.features.layout_category.replace(/_/g, " ")}</Tag> : null}
        </div>
      </div>
    </Link>
  );
}

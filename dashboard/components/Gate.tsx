"use client";

import type { ReactNode } from "react";
import type { LoadResult } from "@/lib/types";
import { EmptyState, LoadingState } from "./ui";

/**
 * Renders children only when a data file loaded successfully; otherwise a loading or
 * explanatory empty state (reason comes from the loader — which file, which pipeline step).
 */
export function Gate<T>({
  loading, result, title, children,
}: {
  loading: boolean;
  result: LoadResult<T> | undefined;
  title: string;
  children: (data: T) => ReactNode;
}) {
  if (loading) return <LoadingState />;
  if (!result || result.status !== "ok" || result.data === null) {
    return <EmptyState title={result?.status === "error" ? `${title}: data could not be read` : title} reason={result?.reason ?? "No data export found."} />;
  }
  return <>{children(result.data)}</>;
}

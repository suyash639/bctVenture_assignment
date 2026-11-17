"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { loadAll } from "@/lib/data";
import type { Ad, DashboardData } from "@/lib/types";

interface DataState {
  loading: boolean;
  data: DashboardData | null;
  /** ad_id -> Ad, for O(1) lookups from cluster / insight references. */
  adIndex: Map<string, Ad>;
}

const DataContext = createContext<DataState>({ loading: true, data: null, adIndex: new Map() });

/** Loads every export file once per page view and shares it with all pages. */
export function DataProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DataState>({ loading: true, data: null, adIndex: new Map() });
  useEffect(() => {
    let alive = true;
    loadAll().then((data) => {
      if (!alive) return;
      const adIndex = new Map((data.ads.data ?? []).map((a) => [a.ad_id, a] as const));
      setState({ loading: false, data, adIndex });
    });
    return () => {
      alive = false;
    };
  }, []);
  return <DataContext.Provider value={state}>{children}</DataContext.Provider>;
}

export const useDashboardData = () => useContext(DataContext);

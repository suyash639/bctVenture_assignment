"use client";

/**
 * Chart wrappers over Recharts. Each takes already-computed rows (from the export) and renders
 * axes with labels, a legend where there is more than one series, and an accessible data table.
 */
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Scatter, ScatterChart,
  Tooltip, XAxis, YAxis, ZAxis,
} from "recharts";
import { DataTable } from "../ui";

const AXIS = { fontSize: 11, fill: "#475569" };

/** Single-series count bar chart (vertical bars). */
export function CountBarChart({
  rows, xLabel, yLabel = "Ads (n)", colourFor, caption, height = 240,
}: {
  rows: { key: string; count: number }[];
  xLabel: string;
  yLabel?: string;
  colourFor?: (key: string, i: number) => string;
  caption: string;
  height?: number;
}) {
  return (
    <>
      <div style={{ height }} aria-hidden>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 28, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="key" tick={AXIS} interval={0} label={{ value: xLabel, position: "insideBottom", offset: -18, ...AXIS }} />
            <YAxis allowDecimals={false} tick={AXIS} label={{ value: yLabel, angle: -90, position: "insideLeft", ...AXIS }} />
            <Tooltip cursor={{ fill: "#f1f5f9" }} />
            <Bar dataKey="count" name={yLabel} isAnimationActive={false}>
              {rows.map((r, i) => (
                <Cell key={r.key} fill={colourFor ? colourFor(r.key, i) : "#4f46e5"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <DataTable caption={caption} headers={[xLabel, yLabel]} rows={rows.map((r) => [r.key, r.count])} />
    </>
  );
}

/**
 * 100%-stacked horizontal bars: one bar per category (e.g. brand), segments = series shares.
 * `rows[i][seriesKey]` are shares in [0,1]; `n` per row is shown in the label.
 */
export function StackedShareChart({
  rows, series, caption, height,
}: {
  rows: ({ category: string; n: number } & Record<string, number | string>)[];
  series: { key: string; label: string; colour: string }[];
  caption: string;
  height?: number;
}) {
  const data = rows.map((r) => ({ ...r, label: `${r.category} (n=${r.n})` }));
  return (
    <>
      <div style={{ height: height ?? Math.max(160, 48 * rows.length + 80) }} aria-hidden>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" stackOffset="expand" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
            <XAxis type="number" tickFormatter={(v: number) => `${Math.round(v * 100)}%`} tick={AXIS} />
            <YAxis type="category" dataKey="label" width={170} tick={AXIS} />
            <Tooltip formatter={(v: number, name: string) => [`${(100 * v).toFixed(1)}%`, name]} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {series.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.label} stackId="a" fill={s.colour} stroke="#ffffff" strokeWidth={0.5} isAnimationActive={false} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <DataTable
        caption={caption}
        headers={["Category", "n", ...series.map((s) => s.label)]}
        rows={rows.map((r) => [r.category, r.n, ...series.map((s) => `${(100 * Number(r[s.key] ?? 0)).toFixed(1)}%`)])}
      />
    </>
  );
}

export interface ScatterPoint {
  id: string;
  x: number;
  y: number;
  group: string;
}

/**
 * Scatter grouped by `group` (colour per group). Used for the PCA projection and strip plots.
 * onPointClick receives the point id (an ad_id).
 */
export function GroupedScatter({
  points, groups, xLabel, yLabel, caption, onPointClick, height = 360, xTicks, xTickFormatter, highlight,
}: {
  points: ScatterPoint[];
  groups: { key: string; label: string; colour: string }[];
  xLabel: string;
  yLabel: string;
  caption: string;
  onPointClick?: (id: string) => void;
  height?: number;
  xTicks?: number[];
  xTickFormatter?: (v: number) => string;
  highlight?: string | null;
}) {
  return (
    <>
      <div style={{ height }} aria-hidden>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 16, bottom: 28, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis type="number" dataKey="x" name={xLabel} tick={AXIS} ticks={xTicks} tickFormatter={xTickFormatter}
              domain={xTicks ? [-0.6, (xTicks.length - 1) + 0.6] : ["auto", "auto"]}
              label={{ value: xLabel, position: "insideBottom", offset: -18, ...AXIS }} />
            <YAxis type="number" dataKey="y" name={yLabel} tick={AXIS} label={{ value: yLabel, angle: -90, position: "insideLeft", ...AXIS }} />
            <ZAxis range={[48, 48]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ payload }) => {
                const p = payload?.[0]?.payload as ScatterPoint | undefined;
                if (!p) return null;
                return (
                  <div className="rounded border border-slate-200 bg-white px-2 py-1 text-xs shadow">
                    <p className="font-mono">{p.id}</p>
                    <p className="text-slate-500">{groups.find((g) => g.key === p.group)?.label ?? p.group}</p>
                  </div>
                );
              }}
            />
            <Legend verticalAlign="top" height={32} wrapperStyle={{ fontSize: 11 }} />
            {groups.map((g) => (
              <Scatter
                key={g.key}
                name={g.label}
                data={points.filter((p) => p.group === g.key)}
                fill={g.colour}
                fillOpacity={highlight && highlight !== g.key ? 0.25 : 0.9}
                isAnimationActive={false}
                cursor={onPointClick ? "pointer" : undefined}
                onClick={(d: unknown) => {
                  const id = (d as { payload?: ScatterPoint; id?: string })?.payload?.id ?? (d as { id?: string })?.id;
                  if (id && onPointClick) onPointClick(id);
                }}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <DataTable caption={caption} headers={["Ad ID", "Group", xLabel, yLabel]} rows={points.map((p) => [p.id, groups.find((g) => g.key === p.group)?.label ?? p.group, p.x.toFixed(3), p.y.toFixed(3)])} />
    </>
  );
}

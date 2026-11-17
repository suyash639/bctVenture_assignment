import type { DominantColour } from "@/lib/types";

/** Horizontal bar of an ad's dominant colours, widths = exported proportions. */
export function ColourSwatchBar({ colours, label }: { colours: DominantColour[]; label: string }) {
  const total = colours.reduce((s, c) => s + c.proportion, 0) || 1;
  return (
    <div role="img" aria-label={label} className="flex h-5 w-full overflow-hidden rounded border border-slate-200">
      {colours.map((c, i) => (
        <div
          key={`${c.hex}-${i}`}
          title={`${c.hex} · ${(100 * c.proportion).toFixed(1)}%`}
          style={{ backgroundColor: c.hex, width: `${(100 * c.proportion) / total}%` }}
        />
      ))}
    </div>
  );
}

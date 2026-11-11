import { useState, type ReactNode } from "react";
import { PlotFigure } from "./plot";

/** A chart with a "Show table" switch; the table holds the same numbers as the chart. */
export function ChartTable({
  label,
  make,
  deps,
  table,
  caption,
}: {
  label: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  make: (w: number) => any;
  deps: unknown[];
  table: ReactNode;
  caption?: ReactNode;
}) {
  const [showTable, setShowTable] = useState(false);
  return (
    <figure className="not-prose m-0 font-sans">
      <div className="mb-2 flex justify-end">
        <button type="button" aria-pressed={showTable} onClick={() => setShowTable(!showTable)}
          className="rounded-md border border-zinc-300 px-3 py-1 text-sm dark:border-zinc-600">
          {showTable ? "Show chart" : "Show table"}
        </button>
      </div>
      {showTable ? <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={`${label} (table)`}>{table}</div> : <PlotFigure label={label} make={make} deps={deps} />}
      {caption && <figcaption className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">{caption}</figcaption>}
    </figure>
  );
}
export function PostHoc() {
  return <span className="ml-1 rounded bg-amber-200 px-1 text-[11px] font-semibold whitespace-nowrap text-amber-950">post hoc</span>;
}
export const tableCls = "w-full text-sm [&_td]:px-2 [&_td]:py-1 [&_th]:px-2 [&_th]:py-1 [&_thead_th]:border-b [&_thead_th]:border-zinc-300 dark:[&_thead_th]:border-zinc-600";

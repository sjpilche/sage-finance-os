"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  align?: "left" | "right" | "center";
  sortable?: boolean;
  className?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface DataTableProps<T extends Record<string, any>> {
  columns: Column<T>[];
  data: T[];
  keyField: string;
  emptyMessage?: string;
  className?: string;
  onRowClick?: (row: T) => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  keyField,
  emptyMessage = "No data available",
  className,
  onRowClick,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollRight, setCanScrollRight] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const check = () => setCanScrollRight(el.scrollWidth > el.clientWidth + el.scrollLeft + 1);
    check();
    el.addEventListener("scroll", check);
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => { el.removeEventListener("scroll", check); ro.disconnect(); };
  }, [data]);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir]);

  if (data.length === 0) {
    return (
      <div className="bg-[var(--surface)] rounded-lg border border-[var(--border)] shadow-sm p-8 text-center text-sm text-[var(--text-secondary)]">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={cn("bg-[var(--surface)] rounded-lg border border-[var(--border)] shadow-sm overflow-hidden relative", className)}>
      {canScrollRight && (
        <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-[var(--surface)] to-transparent z-10 pointer-events-none" />
      )}
      <div ref={scrollRef} className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-[var(--bg-secondary)] border-b border-[var(--border)]">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "px-4 py-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] whitespace-nowrap",
                    col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                    col.sortable && "cursor-pointer select-none hover:bg-slate-200/60 transition-colors",
                    col.className
                  )}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                  aria-sort={col.sortable && sortKey === col.key ? (sortDir === "asc" ? "ascending" : "descending") : col.sortable ? "none" : undefined}
                >
                  {col.header}
                  {col.sortable && sortKey === col.key && (
                    <span className="ml-1.5 text-slate-400">{sortDir === "asc" ? "\u2191" : "\u2193"}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, idx) => (
              <tr
                key={String(row[keyField])}
                className={cn(
                  "border-t border-[var(--border)] transition-colors",
                  idx % 2 === 1 && "bg-[var(--bg-secondary)]/50",
                  onRowClick && "cursor-pointer hover:bg-[var(--bg-hover)] focus-within:bg-[var(--bg-hover)]"
                )}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                onKeyDown={onRowClick ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowClick(row); } } : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                role={onRowClick ? "button" : undefined}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(
                      "px-4 py-2.5",
                      col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                      col.className
                    )}
                  >
                    {col.render ? col.render(row) : (String(row[col.key] ?? "--"))}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

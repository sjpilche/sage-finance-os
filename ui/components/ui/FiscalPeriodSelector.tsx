"use client";

interface FiscalPeriodSelectorProps {
  fiscalYear: number;
  fiscalPeriod?: number;
  onYearChange: (year: number) => void;
  onPeriodChange?: (period: number | undefined) => void;
  showPeriod?: boolean;
}

const currentYear = new Date().getFullYear();
const years = Array.from({ length: 5 }, (_, i) => currentYear - i);
const periods = Array.from({ length: 12 }, (_, i) => i + 1);

const selectClass =
  "px-3 py-2 rounded-lg border border-slate-300 text-sm font-medium bg-white transition-colors duration-150 hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25 focus:border-[var(--accent)]";

export function FiscalPeriodSelector({
  fiscalYear,
  fiscalPeriod,
  onYearChange,
  onPeriodChange,
  showPeriod = true,
}: FiscalPeriodSelectorProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-500">Year</label>
        <select
          value={fiscalYear}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className={selectClass}
        >
          {years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>
      {showPeriod && onPeriodChange && (
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium uppercase tracking-wide text-slate-500">Period</label>
          <select
            value={fiscalPeriod ?? ""}
            onChange={(e) => onPeriodChange(e.target.value ? Number(e.target.value) : undefined)}
            className={selectClass}
          >
            <option value="">All</option>
            {periods.map((p) => (
              <option key={p} value={p}>P{p}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

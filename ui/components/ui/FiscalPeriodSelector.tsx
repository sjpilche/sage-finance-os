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

export function FiscalPeriodSelector({
  fiscalYear,
  fiscalPeriod,
  onYearChange,
  onPeriodChange,
  showPeriod = true,
}: FiscalPeriodSelectorProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        <label className="text-sm text-slate-500">Year</label>
        <select
          value={fiscalYear}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="px-2 py-1.5 rounded border border-slate-200 text-sm bg-white"
        >
          {years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>
      {showPeriod && onPeriodChange && (
        <div className="flex items-center gap-1.5">
          <label className="text-sm text-slate-500">Period</label>
          <select
            value={fiscalPeriod ?? ""}
            onChange={(e) => onPeriodChange(e.target.value ? Number(e.target.value) : undefined)}
            className="px-2 py-1.5 rounded border border-slate-200 text-sm bg-white"
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

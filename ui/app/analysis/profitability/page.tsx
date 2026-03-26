"use client";

import { useState } from "react";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { KpiCard } from "@/components/ui/KpiCard";
import { Card } from "@/components/ui/Card";
import { FiscalPeriodSelector } from "@/components/ui/FiscalPeriodSelector";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { ProfitabilityChart } from "@/components/charts/ProfitabilityChart";
import { formatCurrency, formatPct } from "@/lib/utils";
import type { ProfitabilityReport, ProfitabilitySegment } from "@/lib/types/analysis";

const dimensionLabels: Record<string, string> = {
  dimension_1: "Department",
  dimension_2: "Location",
  dimension_3: "Class",
};

const columns: Column<ProfitabilitySegment>[] = [
  { key: "dimension_value", header: "Segment", sortable: true },
  {
    key: "revenue",
    header: "Revenue",
    align: "right",
    render: (row) => <span className="font-mono">{formatCurrency(row.revenue)}</span>,
    sortable: true,
  },
  {
    key: "expenses",
    header: "Expenses",
    align: "right",
    render: (row) => <span className="font-mono">{formatCurrency(row.expenses)}</span>,
    sortable: true,
  },
  {
    key: "net_income",
    header: "Net Income",
    align: "right",
    render: (row) => (
      <span className={`font-mono font-medium ${row.net_income >= 0 ? "text-green-600" : "text-red-600"}`}>
        {formatCurrency(row.net_income)}
      </span>
    ),
    sortable: true,
  },
  {
    key: "margin_pct",
    header: "Margin",
    align: "right",
    render: (row) => (
      <span className={`font-mono ${row.margin_pct >= 0 ? "text-green-600" : "text-red-600"}`}>
        {formatPct(row.margin_pct)}
      </span>
    ),
    sortable: true,
  },
];

export default function ProfitabilityPage() {
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());
  const [fiscalPeriod, setFiscalPeriod] = useState<number | undefined>(undefined);
  const [dimension, setDimension] = useState("dimension_1");

  const periodParam = fiscalPeriod ? `&fiscal_period=${fiscalPeriod}` : "";
  const { data, error, isLoading } = useApi<ProfitabilityReport>(
    `/v1/analysis/profitability?fiscal_year=${fiscalYear}&dimension=${dimension}${periodParam}`
  );

  const report = data?.data;

  return (
    <div>
      <PageHeader
        title="Profitability Analysis"
        subtitle={`Revenue, expenses, and margins by ${dimensionLabels[dimension] || dimension}`}
        actions={
          <div className="flex items-center gap-4">
            <FiscalPeriodSelector
              fiscalYear={fiscalYear}
              fiscalPeriod={fiscalPeriod}
              onYearChange={setFiscalYear}
              onPeriodChange={setFiscalPeriod}
            />
            <div className="flex items-center gap-1.5">
              <label className="text-sm text-slate-500">Dimension</label>
              <select
                value={dimension}
                onChange={(e) => setDimension(e.target.value)}
                className="px-2 py-1.5 rounded border border-slate-200 text-sm bg-white"
              >
                <option value="dimension_1">Department</option>
                <option value="dimension_2">Location</option>
                <option value="dimension_3">Class</option>
              </select>
            </div>
          </div>
        }
      />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {report && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Total Revenue" value={formatCurrency(report.summary.total_revenue)} />
            <KpiCard label="Total Expenses" value={formatCurrency(report.summary.total_expenses)} />
            <KpiCard
              label="Net Income"
              value={formatCurrency(report.summary.total_net_income)}
              trend={report.summary.total_net_income >= 0 ? "up" : "down"}
            />
            <KpiCard
              label="Overall Margin"
              value={formatPct(report.summary.total_margin_pct)}
              trend={report.summary.total_margin_pct >= 0 ? "up" : "down"}
            />
          </div>

          {/* Chart */}
          <Card title={`Revenue vs Expenses by ${dimensionLabels[dimension] || dimension}`}>
            <ProfitabilityChart segments={report.segments} />
          </Card>

          {/* Detail Table */}
          <DataTable
            columns={columns}
            data={report.segments}
            keyField="dimension_value"
            emptyMessage="No profitability data for this period"
          />
        </div>
      )}
    </div>
  );
}

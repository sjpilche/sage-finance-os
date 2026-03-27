"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { KpiCard } from "@/components/ui/KpiCard";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FiscalPeriodSelector } from "@/components/ui/FiscalPeriodSelector";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { VarianceChart } from "@/components/charts/VarianceChart";
import { formatCurrency, formatPct } from "@/lib/utils";
import type { VarianceReport, VarianceDetail } from "@/lib/types/analysis";

const columns: Column<VarianceDetail>[] = [
  { key: "account_number", header: "Account", className: "font-mono", sortable: true },
  { key: "account_name", header: "Name", sortable: true },
  {
    key: "budget",
    header: "Budget",
    align: "right",
    render: (row) => <span className="font-mono">{formatCurrency(row.budget)}</span>,
  },
  {
    key: "actual",
    header: "Actual",
    align: "right",
    render: (row) => <span className="font-mono">{formatCurrency(row.actual)}</span>,
  },
  {
    key: "variance",
    header: "Variance",
    align: "right",
    render: (row) => (
      <span className={`font-mono font-medium ${row.direction === "favorable" ? "text-green-600" : row.direction === "unfavorable" ? "text-red-600" : ""}`}>
        {formatCurrency(row.variance)}
      </span>
    ),
    sortable: true,
  },
  {
    key: "variance_pct",
    header: "Var %",
    align: "right",
    render: (row) => <span className="font-mono">{formatPct(row.variance_pct)}</span>,
    sortable: true,
  },
  {
    key: "direction",
    header: "Direction",
    render: (row) => (
      <Badge variant={row.direction === "favorable" ? "success" : row.direction === "unfavorable" ? "danger" : "default"}>
        {row.direction}
      </Badge>
    ),
  },
];

export default function VariancePage() {
  const router = useRouter();
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());
  const [fiscalPeriod, setFiscalPeriod] = useState<number | undefined>(undefined);
  const [threshold, setThreshold] = useState(10);

  const periodParam = fiscalPeriod ? `&fiscal_period=${fiscalPeriod}` : "";
  const { data, error, isLoading } = useApi<VarianceReport>(
    `/v1/analysis/variance?fiscal_year=${fiscalYear}&threshold_pct=${threshold}${periodParam}`
  );

  const report = data?.data;

  return (
    <div>
      <PageHeader
        title="Variance Analysis"
        subtitle="Budget vs actual comparison"
        actions={
          <div className="flex flex-wrap items-center gap-2 sm:gap-4">
            <FiscalPeriodSelector
              fiscalYear={fiscalYear}
              fiscalPeriod={fiscalPeriod}
              onYearChange={setFiscalYear}
              onPeriodChange={setFiscalPeriod}
            />
            <div className="flex items-center gap-1.5">
              <label className="text-sm text-[var(--text-secondary)]">Threshold</label>
              <select
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="px-2 py-1.5 rounded border border-[var(--border)] text-sm bg-[var(--surface)]"
              >
                {[5, 10, 15, 20, 25].map((t) => (
                  <option key={t} value={t}>{t}%</option>
                ))}
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
            <KpiCard label="Total Budget" value={formatCurrency(report.summary.total_budget)} />
            <KpiCard label="Total Actual" value={formatCurrency(report.summary.total_actual)} />
            <KpiCard
              label="Total Variance"
              value={formatCurrency(report.summary.total_variance)}
              trend={report.summary.total_variance >= 0 ? "up" : "down"}
            />
            <KpiCard
              label="Flagged Accounts"
              value={`${report.summary.accounts_flagged} / ${report.summary.accounts_analyzed}`}
              trend={report.summary.accounts_flagged === 0 ? "up" : "down"}
            />
          </div>

          {/* Variance Chart */}
          <Card title="Flagged Accounts">
            <VarianceChart details={report.details} />
          </Card>

          {/* Detail Table — click to drill into GL */}
          <DataTable
            columns={columns}
            data={report.details}
            keyField="account_number"
            emptyMessage="No variance data for this period"
            onRowClick={(row) => router.push(`/data/gl?account=${encodeURIComponent(row.account_number)}`)}
          />
        </div>
      )}
    </div>
  );
}

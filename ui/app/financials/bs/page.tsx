"use client";

import { useState } from "react";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { FiscalPeriodSelector } from "@/components/ui/FiscalPeriodSelector";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatCurrency } from "@/lib/utils";
import type { BalanceSheetResponse } from "@/lib/types/semantic";

export default function BalanceSheetPage() {
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());

  const { data, error, isLoading } = useApi<BalanceSheetResponse>(
    `/v1/semantic/financials/bs?fiscal_year=${fiscalYear}`
  );

  const bs = data?.data;

  return (
    <div>
      <PageHeader
        title="Balance Sheet"
        subtitle={bs ? `FY${bs.fiscal_year}` : undefined}
        actions={
          <FiscalPeriodSelector
            fiscalYear={fiscalYear}
            onYearChange={setFiscalYear}
            showPeriod={false}
          />
        }
      />

      {isLoading && <LoadingState message="Loading balance sheet..." />}
      {error && <ErrorState message={error.message} />}

      {bs && (
        <div className="space-y-6">
          {/* Accounting Equation */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-8">
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
              <div className="text-center bg-teal-50 rounded-lg px-6 py-4 min-w-[160px]">
                <div className="text-xs font-semibold uppercase tracking-wide text-teal-700 mb-2">Assets</div>
                <div className="text-2xl font-bold text-slate-900 tabular-nums">{formatCurrency(bs.total_assets)}</div>
              </div>
              <span className="text-3xl text-slate-300 font-light">=</span>
              <div className="text-center bg-red-50 rounded-lg px-6 py-4 min-w-[160px]">
                <div className="text-xs font-semibold uppercase tracking-wide text-red-700 mb-2">Liabilities</div>
                <div className="text-2xl font-bold text-slate-900 tabular-nums">{formatCurrency(bs.total_liabilities)}</div>
              </div>
              <span className="text-3xl text-slate-300 font-light">+</span>
              <div className="text-center bg-blue-50 rounded-lg px-6 py-4 min-w-[160px]">
                <div className="text-xs font-semibold uppercase tracking-wide text-blue-700 mb-2">Equity</div>
                <div className="text-2xl font-bold text-slate-900 tabular-nums">{formatCurrency(bs.total_equity)}</div>
              </div>
            </div>
          </div>

          {/* Section Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(bs.sections).map(([accountType, amount]) => (
              <Card key={accountType} title={accountType}>
                <div className="text-xl font-bold text-slate-900 font-mono">
                  {formatCurrency(amount)}
                </div>
              </Card>
            ))}
          </div>

          {bs.total_assets === 0 && bs.total_liabilities === 0 && bs.total_equity === 0 && (
            <EmptyState message="No balance sheet data for this fiscal year" />
          )}
        </div>
      )}
    </div>
  );
}

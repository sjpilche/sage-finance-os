"use client";

import { useState } from "react";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { FiscalPeriodSelector } from "@/components/ui/FiscalPeriodSelector";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatementTable } from "@/components/tables/StatementTable";
import type { IncomeStatementResponse } from "@/lib/types/semantic";

export default function IncomeStatementPage() {
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());
  const [fiscalPeriod, setFiscalPeriod] = useState<number | undefined>(undefined);

  const periodParam = fiscalPeriod ? `&fiscal_period=${fiscalPeriod}` : "";
  const { data, error, isLoading } = useApi<IncomeStatementResponse>(
    `/v1/semantic/financials/pl?fiscal_year=${fiscalYear}${periodParam}`
  );

  const statement = data?.data;

  return (
    <div>
      <PageHeader
        title="Income Statement"
        subtitle={statement ? `FY${statement.fiscal_year}${statement.fiscal_period ? ` P${statement.fiscal_period}` : ""}` : undefined}
        actions={
          <FiscalPeriodSelector
            fiscalYear={fiscalYear}
            fiscalPeriod={fiscalPeriod}
            onYearChange={setFiscalYear}
            onPeriodChange={setFiscalPeriod}
          />
        }
      />

      {isLoading && <LoadingState message="Loading income statement..." />}
      {error && <ErrorState message={error.message} />}
      {statement && statement.lines.length === 0 && (
        <EmptyState message="No income statement data for this period" />
      )}
      {statement && statement.lines.length > 0 && (
        <StatementTable lines={statement.lines} />
      )}
    </div>
  );
}

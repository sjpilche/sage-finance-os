"use client";

import { useState } from "react";
import { useApi, apiMutate } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FiscalPeriodSelector } from "@/components/ui/FiscalPeriodSelector";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { formatPct } from "@/lib/utils";
import { CheckCircle, XCircle } from "lucide-react";
import type { CloseChecklist, CloseCheckItem } from "@/lib/types/platform";
import type { PeriodStatus } from "@/lib/types/semantic";

const periodColumns: Column<PeriodStatus>[] = [
  { key: "fiscal_year", header: "Year", sortable: true },
  { key: "fiscal_period", header: "Period", render: (row) => `P${row.fiscal_period}`, sortable: true },
  {
    key: "status",
    header: "Status",
    render: (row) => (
      <Badge variant={row.status === "closed" || row.status === "locked" ? "success" : row.status === "closing" ? "warning" : "default"}>
        {row.status}
      </Badge>
    ),
  },
  { key: "closed_by", header: "Closed By", render: (row) => row.closed_by || "--" },
  { key: "closed_at", header: "Closed At", render: (row) => row.closed_at ? new Date(row.closed_at).toLocaleString() : "--" },
];

export default function PeriodClosePage() {
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());
  const [fiscalPeriod, setFiscalPeriod] = useState<number | undefined>(new Date().getMonth() + 1);
  const [closing, setClosing] = useState(false);
  const [closeError, setCloseError] = useState<string | null>(null);

  const periodParam = fiscalPeriod ? `&fiscal_period=${fiscalPeriod}` : "";
  const { data: checklistData, error: checklistError, isLoading: checklistLoading, mutate } =
    useApi<CloseChecklist>(
      fiscalPeriod ? `/v1/analysis/close-checklist?fiscal_year=${fiscalYear}${periodParam}` : null
    );
  const { data: periodsData } = useApi<PeriodStatus[]>(`/v1/semantic/periods?fiscal_year=${fiscalYear}`);

  const checklist = checklistData?.data;
  const periods = periodsData?.data || [];

  const handleClose = async () => {
    if (!fiscalPeriod || !checklist) return;
    setClosing(true);
    setCloseError(null);
    try {
      await apiMutate("/v1/semantic/periods/close", "POST", {
        fiscal_year: fiscalYear,
        fiscal_period: fiscalPeriod,
        actor: "ui-user",
      });
      mutate();
    } catch (err) {
      setCloseError(err instanceof Error ? err.message : "Failed to close period");
    } finally {
      setClosing(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Period Close"
        subtitle="Review readiness checklist and close fiscal periods"
        actions={
          <FiscalPeriodSelector
            fiscalYear={fiscalYear}
            fiscalPeriod={fiscalPeriod}
            onYearChange={(y) => { setFiscalYear(y); setCloseError(null); }}
            onPeriodChange={(p) => { setFiscalPeriod(p); setCloseError(null); }}
          />
        }
      />

      {checklistLoading && <LoadingState />}
      {checklistError && <ErrorState message={checklistError.message} />}

      {checklist && (
        <div className="space-y-6">
          {/* Readiness Bar */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="text-lg font-bold text-slate-900">
                  {formatPct(checklist.readiness_pct)}
                </span>
                <span className="text-sm text-slate-500 ml-2">
                  ready ({checklist.passed}/{checklist.total} checks passed)
                </span>
              </div>
              <button
                onClick={handleClose}
                disabled={closing || !checklist.ready_to_close}
                className="px-4 py-2 rounded-lg text-sm font-medium text-white bg-[var(--accent)] hover:bg-[var(--accent-light)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {closing ? "Closing..." : `Close P${fiscalPeriod}`}
              </button>
            </div>
            {closeError && <p className="text-sm text-red-600 mt-2">{closeError}</p>}
            <div className="w-full bg-slate-200 rounded-full h-2.5">
              <div
                className="h-2.5 rounded-full transition-all"
                style={{
                  width: `${checklist.readiness_pct}%`,
                  backgroundColor: checklist.readiness_pct === 100 ? "var(--success)" : checklist.readiness_pct >= 70 ? "var(--warning)" : "var(--danger)",
                }}
              />
            </div>
          </Card>

          {/* Checklist Items */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {checklist.checks.map((check: CloseCheckItem) => (
              <Card key={check.check} className="flex items-start gap-3">
                {check.passed ? (
                  <CheckCircle size={20} className="text-green-500 shrink-0 mt-0.5" />
                ) : (
                  <XCircle size={20} className="text-red-500 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="text-sm font-medium text-slate-800">{check.display}</div>
                  {Object.entries(check.details).length > 0 && (
                    <div className="text-xs text-slate-500 mt-0.5">
                      {Object.entries(check.details).map(([k, v]) => (
                        <span key={k} className="mr-3">{k}: {String(v)}</span>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>

          {/* Period Status History */}
          <div>
            <h2 className="text-lg font-semibold text-slate-800 mb-3">Period Status</h2>
            <DataTable
              columns={periodColumns}
              data={periods}
              keyField="fiscal_period"
              emptyMessage="No period data for this fiscal year"
            />
          </div>
        </div>
      )}

      {!fiscalPeriod && !checklistLoading && (
        <Card className="text-center py-8">
          <p className="text-sm text-slate-500">Select a fiscal period to view the close checklist</p>
        </Card>
      )}
    </div>
  );
}

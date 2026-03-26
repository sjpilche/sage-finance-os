"use client";

import { useRouter } from "next/navigation";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { KpiCard } from "@/components/ui/KpiCard";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { QualityRadarChart } from "@/components/charts/RadarChart";
import { formatDateTime, formatPct } from "@/lib/utils";
import type { Scorecard } from "@/lib/types/quality";

const gateVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  certified: "success",
  conditional: "warning",
  failed: "danger",
  pending: "default",
};

const columns: Column<Scorecard>[] = [
  {
    key: "created_at",
    header: "Date",
    render: (row) => <span className="text-slate-600">{formatDateTime(row.created_at)}</span>,
    sortable: true,
  },
  {
    key: "composite",
    header: "Composite",
    align: "right",
    render: (row) => <span className="font-mono font-medium">{formatPct(row.composite)}</span>,
    sortable: true,
  },
  {
    key: "accuracy",
    header: "Accuracy",
    align: "right",
    render: (row) => <span className="font-mono">{formatPct(row.accuracy)}</span>,
  },
  {
    key: "completeness",
    header: "Complete",
    align: "right",
    render: (row) => <span className="font-mono">{formatPct(row.completeness)}</span>,
  },
  {
    key: "gate_status",
    header: "Verdict",
    render: (row) => (
      <Badge variant={gateVariant[row.gate_status] || "default"}>
        {row.gate_status.toUpperCase()}
      </Badge>
    ),
  },
];

export default function QualityPage() {
  const router = useRouter();
  const { data, error, isLoading } = useApi<Scorecard[]>("/v1/quality/scorecards?limit=20");

  const scorecards = data?.data || [];
  const latest = scorecards[0];

  return (
    <div>
      <PageHeader title="Data Quality" subtitle="Trust scorecards and DQ check results" />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {!isLoading && !error && (
        <div className="space-y-6">
          {/* Latest Scorecard Summary */}
          {latest && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <Card title="Latest Scorecard" className="lg:col-span-2">
                <QualityRadarChart scorecard={latest} />
              </Card>
              <div className="space-y-4">
                <KpiCard
                  label="Composite Score"
                  value={formatPct(latest.composite)}
                  trend={latest.composite >= 98 ? "up" : latest.composite >= 90 ? "neutral" : "down"}
                />
                <KpiCard
                  label="Accuracy Gate"
                  value={formatPct(latest.accuracy)}
                  trend={latest.accuracy === 100 ? "up" : "down"}
                />
                <Card>
                  <div className="text-sm text-slate-500 mb-1">Verdict</div>
                  <Badge variant={gateVariant[latest.gate_status] || "default"}>
                    {latest.gate_status.toUpperCase()}
                  </Badge>
                </Card>
              </div>
            </div>
          )}

          {/* Scorecard History */}
          <DataTable
            columns={columns}
            data={scorecards}
            keyField="scorecard_id"
            emptyMessage="No scorecards yet. Run a sync to generate quality scores."
            onRowClick={(row) => router.push(`/quality/${row.run_id}`)}
          />
        </div>
      )}
    </div>
  );
}

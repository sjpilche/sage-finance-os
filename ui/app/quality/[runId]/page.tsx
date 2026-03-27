"use client";

import { useParams } from "next/navigation";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import type { DQChecksResponse, DQCheck } from "@/lib/types/quality";
import { formatPct } from "@/lib/utils";
import { Breadcrumb } from "@/components/ui/Breadcrumb";

const severityVariant: Record<string, "danger" | "warning" | "info" | "default"> = {
  critical: "danger",
  high: "danger",
  medium: "warning",
  low: "info",
};

const columns: Column<DQCheck>[] = [
  { key: "check_name", header: "Check", sortable: true },
  { key: "object_name", header: "Object", sortable: true },
  {
    key: "passed",
    header: "Result",
    render: (row) => (
      <Badge variant={row.passed ? "success" : "danger"}>
        {row.passed ? "PASS" : "FAIL"}
      </Badge>
    ),
  },
  {
    key: "severity",
    header: "Severity",
    render: (row) => (
      <Badge variant={severityVariant[row.severity] || "default"}>
        {row.severity}
      </Badge>
    ),
  },
];

export default function QualityDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const { data, error, isLoading } = useApi<DQChecksResponse>(
    runId ? `/v1/quality/checks/${runId}` : null
  );

  const checks = data?.data;

  return (
    <div>
      <Breadcrumb items={[
        { label: "Dashboard", href: "/" },
        { label: "Quality", href: "/quality" },
        { label: runId ? `Run ${runId.slice(0, 8)}` : "Detail" },
      ]} />

      <PageHeader
        title="DQ Check Results"
        subtitle={
          checks
            ? `Run ${runId?.slice(0, 8)} \u2014 ${checks.passed}/${checks.total} passed (${formatPct(checks.pass_rate * 100)})`
            : undefined
        }
      />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {checks && (
        <DataTable
          columns={columns}
          data={checks.checks}
          keyField="result_id"
          emptyMessage="No DQ checks found for this run"
        />
      )}
    </div>
  );
}

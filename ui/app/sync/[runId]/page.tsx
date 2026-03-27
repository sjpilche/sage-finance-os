"use client";

import { useParams } from "next/navigation";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { formatDateTime } from "@/lib/utils";
import Link from "next/link";
import { Breadcrumb } from "@/components/ui/Breadcrumb";
import type { SyncRun } from "@/lib/types/platform";

export default function SyncDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const { data, error, isLoading } = useApi<SyncRun>(
    runId ? `/v1/sync/runs/${runId}` : null
  );

  const run = data?.data;

  return (
    <div>
      <Breadcrumb items={[
        { label: "Dashboard", href: "/" },
        { label: "Sync Runs", href: "/sync" },
        { label: runId ? `Run ${runId.slice(0, 8)}` : "Detail" },
      ]} />

      <PageHeader title="Sync Run Detail" subtitle={runId ? `Run ${runId.slice(0, 8)}...` : ""} />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {run && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="Status">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-slate-500">Status</span>
                <StatusBadge status={run.status} />
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-500">Mode</span>
                <span className="text-sm capitalize">{run.mode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-500">Started</span>
                <span className="text-sm">{formatDateTime(run.started_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-500">Completed</span>
                <span className="text-sm">{run.completed_at ? formatDateTime(run.completed_at) : "--"}</span>
              </div>
            </div>
          </Card>

          {run.error_message && (
            <Card title="Error">
              <p className="text-sm text-red-600 whitespace-pre-wrap">{run.error_message}</p>
            </Card>
          )}

          {run.summary && Object.keys(run.summary).length > 0 && (
            <Card title="Summary">
              <div className="space-y-1.5">
                {Object.entries(run.summary).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-slate-500">{key}</span>
                    <span className="font-mono">{String(value)}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <Card title="Actions">
            <Link
              href={`/quality/${run.run_id}`}
              className="text-sm text-[var(--accent)] hover:underline"
            >
              View Quality Checks
            </Link>
          </Card>
        </div>
      )}
    </div>
  );
}

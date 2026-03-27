"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApi, apiMutate } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Modal } from "@/components/ui/Modal";
import { formatDateTime } from "@/lib/utils";
import { Play, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import type { SyncRun, Connection } from "@/lib/types/platform";

const columns: Column<SyncRun>[] = [
  {
    key: "started_at",
    header: "Started",
    render: (row) => <span className="text-slate-600">{formatDateTime(row.started_at)}</span>,
    sortable: true,
  },
  { key: "mode", header: "Mode", render: (row) => <span className="capitalize">{row.mode}</span> },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.status} />,
  },
  {
    key: "completed_at",
    header: "Completed",
    render: (row) => <span className="text-slate-500">{row.completed_at ? formatDateTime(row.completed_at) : "--"}</span>,
  },
  {
    key: "error_message",
    header: "Error",
    render: (row) => row.error_message ? (
      <span className="text-red-600 text-xs truncate max-w-[200px] inline-block">{row.error_message}</span>
    ) : "--",
  },
];

export default function SyncPage() {
  const router = useRouter();
  const { data, error, isLoading, mutate } = useApi<SyncRun[]>("/v1/sync/runs?limit=50");
  const { data: connData } = useApi<Connection[]>("/v1/connections");
  const [showTrigger, setShowTrigger] = useState(false);
  const [selectedConn, setSelectedConn] = useState("");
  const [syncMode, setSyncMode] = useState<"full" | "incremental">("full");
  const [triggering, setTriggering] = useState(false);
  const { toast } = useToast();

  const runs = data?.data || [];
  const connections = connData?.data || [];

  const handleTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConn) return;
    setTriggering(true);
    try {
      await apiMutate("/v1/sync/trigger", "POST", {
        connection_id: selectedConn,
        mode: syncMode,
      });
      setShowTrigger(false);
      mutate();
      toast("Sync triggered successfully", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to trigger sync", "error");
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Sync Runs"
        subtitle="Pipeline execution history"
        actions={
          <button
            onClick={() => setShowTrigger(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white bg-[var(--accent)] hover:bg-[var(--accent-light)] transition-colors"
          >
            <Play size={16} /> Trigger Sync
          </button>
        }
      />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {!isLoading && !error && (
        <DataTable
          columns={columns}
          data={runs}
          keyField="run_id"
          emptyMessage="No sync runs yet. Trigger a sync to get started."
          onRowClick={(row) => router.push(`/sync/${row.run_id}`)}
        />
      )}

      {/* Trigger Modal */}
      <Modal open={showTrigger} onClose={() => setShowTrigger(false)} title="Trigger Sync">
        <form onSubmit={handleTrigger} className="space-y-4">
          <div>
            <label htmlFor="sync-connection" className="block text-sm text-slate-600 mb-1">Connection</label>
            <select
              id="sync-connection"
              required
              value={selectedConn}
              onChange={(e) => setSelectedConn(e.target.value)}
              className="w-full px-3 py-2 rounded border border-slate-200 text-sm bg-white"
            >
              <option value="">Select a connection...</option>
              {connections.map((c) => (
                <option key={c.connection_id} value={c.connection_id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-600 mb-1">Mode</label>
            <div className="flex gap-3">
              {(["full", "incremental"] as const).map((mode) => (
                <label key={mode} className="flex items-center gap-1.5 text-sm">
                  <input
                    type="radio"
                    value={mode}
                    checked={syncMode === mode}
                    onChange={() => setSyncMode(mode)}
                  />
                  <span className="capitalize">{mode}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowTrigger(false)}
              className="px-3 py-2 text-sm rounded border border-slate-200 text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={triggering || !selectedConn}
              className="px-4 py-2 text-sm rounded font-medium text-white bg-[var(--accent)] hover:bg-[var(--accent-light)] disabled:opacity-50"
            >
              {triggering && <Loader2 size={14} className="animate-spin mr-1 inline" />}
              {triggering ? "Starting..." : "Start Sync"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

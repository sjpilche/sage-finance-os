"use client";

import { useState } from "react";
import { useApi, apiMutate } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { formatDateTime } from "@/lib/utils";
import { ShieldAlert, ShieldOff } from "lucide-react";
import type { KillSwitchRule, PlatformEvent } from "@/lib/types/platform";

const eventColumns: Column<PlatformEvent>[] = [
  { key: "created_at", header: "Time", render: (row) => <span className="text-slate-600">{formatDateTime(row.created_at)}</span>, sortable: true },
  { key: "event_type", header: "Type", className: "font-mono", sortable: true },
  { key: "source", header: "Source" },
  {
    key: "payload",
    header: "Payload",
    render: (row) => (
      <span className="text-xs text-slate-500 font-mono truncate max-w-[300px] inline-block">
        {JSON.stringify(row.payload).slice(0, 80)}
      </span>
    ),
  },
];

export default function SettingsPage() {
  const { data: ksData, error: ksError, isLoading: ksLoading, mutate: ksMutate } = useApi<KillSwitchRule[]>("/v1/platform/kill-switch");
  const { data: eventsData, error: eventsError, isLoading: eventsLoading } = useApi<PlatformEvent[]>("/v1/platform/events?limit=50");
  const { data: schedulerData } = useApi<Record<string, unknown>>("/v1/platform/scheduler");
  const [acting, setActing] = useState(false);

  const rules = ksData?.data || [];
  const events = eventsData?.data || [];
  const scheduler = schedulerData?.data;
  const globalRule = rules.find((r) => r.scope === "global");

  const toggleKillSwitch = async () => {
    setActing(true);
    try {
      const action = globalRule?.is_active ? "deactivate" : "activate";
      await apiMutate(`/v1/platform/kill-switch/${action}`, "POST", {
        scope: "global",
        mode: "hard",
        reason: `Manual ${action} from UI`,
        actor: "ui-user",
      });
      ksMutate();
    } finally {
      setActing(false);
    }
  };

  return (
    <div>
      <PageHeader title="Settings" subtitle="Platform operations and monitoring" />

      <div className="space-y-6">
        {/* Kill Switch */}
        <Card title="Kill Switch">
          {ksLoading && <LoadingState />}
          {ksError && <ErrorState message={ksError.message} />}
          {globalRule && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {globalRule.is_active ? (
                  <ShieldAlert size={24} className="text-red-500" />
                ) : (
                  <ShieldOff size={24} className="text-green-500" />
                )}
                <div>
                  <div className="font-medium text-slate-900">
                    Global Kill Switch: <Badge variant={globalRule.is_active ? "danger" : "success"}>{globalRule.is_active ? "ACTIVE" : "Inactive"}</Badge>
                  </div>
                  {globalRule.reason && (
                    <div className="text-xs text-slate-500 mt-0.5">Reason: {globalRule.reason}</div>
                  )}
                </div>
              </div>
              <button
                onClick={toggleKillSwitch}
                disabled={acting}
                className={`px-4 py-2 text-sm rounded font-medium transition-colors ${
                  globalRule.is_active
                    ? "bg-green-600 hover:bg-green-700 text-white"
                    : "bg-red-600 hover:bg-red-700 text-white"
                } disabled:opacity-50`}
              >
                {acting ? "..." : globalRule.is_active ? "Deactivate" : "Activate"}
              </button>
            </div>
          )}
        </Card>

        {/* Scheduler */}
        <Card title="Scheduler Status">
          {scheduler ? (
            <div className="space-y-2">
              {Object.entries(scheduler).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-slate-500">{key}</span>
                  <span className="font-mono">{typeof value === "object" ? JSON.stringify(value) : String(value)}</span>
                </div>
              ))}
              {Object.keys(scheduler).length === 0 && (
                <p className="text-sm text-slate-500">No scheduled jobs</p>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Loading scheduler status...</p>
          )}
        </Card>

        {/* Event Log */}
        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Event Log</h2>
          {eventsLoading && <LoadingState />}
          {eventsError && <ErrorState message={eventsError.message} />}
          {!eventsLoading && !eventsError && (
            <DataTable
              columns={eventColumns}
              data={events}
              keyField="event_id"
              emptyMessage="No events recorded"
            />
          )}
        </div>
      </div>
    </div>
  );
}

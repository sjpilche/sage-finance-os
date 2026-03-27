"use client";

import { useApi } from "@/lib/api/client";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/ui/PageHeader";
import { KpiCard } from "@/components/ui/KpiCard";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Card } from "@/components/ui/Card";
import { formatDateTime, formatNumber } from "@/lib/utils";
import type { FreshnessResponse } from "@/lib/types/platform";
import type { SyncRun } from "@/lib/types/platform";
import type { Scorecard } from "@/lib/types/quality";
import Link from "next/link";
import {
  ArrowRight,
  TrendingUp,
  Timer,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { DashboardSkeleton } from "@/components/ui/Skeleton";

export default function Dashboard() {
  const { data: summary } = useApi<Record<string, number>>("/v1/data/summary");
  const { data: freshness } = useApi<FreshnessResponse>("/v1/platform/freshness");
  const { data: runsData } = useApi<SyncRun[]>("/v1/sync/runs?limit=5");
  const { data: scorecardData } = useApi<Scorecard[]>("/v1/quality/scorecards?limit=1");

  const isLoading = !summary && !freshness;
  const counts = summary?.data || {};
  const lastSync = freshness?.data?.last_sync;
  const runs = runsData?.data || [];
  const latestScorecard = scorecardData?.data?.[0];

  if (isLoading) return <DashboardSkeleton />;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        actions={
          <div className="text-sm text-slate-500">
            Last sync: {lastSync ? formatDateTime(lastSync) : "Never"}
          </div>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <KpiCard label="GL Entries" value={formatNumber(counts.gl_entry)} />
        <KpiCard label="AP Invoices" value={formatNumber(counts.ap_invoice)} />
        <KpiCard label="AR Invoices" value={formatNumber(counts.ar_invoice)} />
        <KpiCard label="Vendors" value={formatNumber(counts.vendor)} />
        <KpiCard label="Customers" value={formatNumber(counts.customer)} />
        <KpiCard label="Chart of Accounts" value={formatNumber(counts.chart_of_accounts)} />
        <KpiCard label="Trial Balance" value={formatNumber(counts.trial_balance)} />
        <KpiCard label="Budget Lines" value={formatNumber(counts.budget_line)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Quick Actions */}
        <Card title="Quick Actions">
          <div className="space-y-2">
            <Link href="/financials/pl" className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 text-sm font-medium text-slate-700 transition-all duration-150">
              <TrendingUp size={16} className="text-[var(--accent)]" />
              Income Statement
              <ArrowRight size={14} className="ml-auto text-slate-400" />
            </Link>
            <Link href="/analysis/aging" className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 text-sm font-medium text-slate-700 transition-all duration-150">
              <Timer size={16} className="text-[var(--accent)]" />
              AR/AP Aging
              <ArrowRight size={14} className="ml-auto text-slate-400" />
            </Link>
            <Link href="/quality" className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 text-sm font-medium text-slate-700 transition-all duration-150">
              <ShieldCheck size={16} className="text-[var(--accent)]" />
              Quality Scorecards
              <ArrowRight size={14} className="ml-auto text-slate-400" />
            </Link>
            <Link href="/sync" className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 text-sm font-medium text-slate-700 transition-all duration-150">
              <RefreshCw size={16} className="text-[var(--accent)]" />
              Sync Runs
              <ArrowRight size={14} className="ml-auto text-slate-400" />
            </Link>
          </div>
        </Card>

        {/* Latest Quality Score */}
        <Card title="Data Quality">
          {latestScorecard ? (
            <div className="text-center">
              <div className="text-3xl font-bold text-slate-900">
                {latestScorecard.composite.toFixed(1)}%
              </div>
              <div className="text-sm text-slate-500 mt-1">Composite Score</div>
              <div className="mt-2">
                <Badge
                  variant={latestScorecard.gate_status === "certified" ? "success" : latestScorecard.gate_status === "conditional" ? "warning" : "danger"}
                >
                  {latestScorecard.gate_status.toUpperCase()}
                </Badge>
              </div>
              <Link href="/quality" className="text-xs text-[var(--accent)] hover:underline mt-3 inline-block">
                View details
              </Link>
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-4">No quality data yet</p>
          )}
        </Card>

        {/* Recent Sync Runs */}
        <Card title="Recent Syncs">
          {runs.length > 0 ? (
            <div className="space-y-2">
              {runs.map((run) => (
                <div key={run.run_id} className="flex items-center justify-between text-sm">
                  <div>
                    <span className="text-slate-600">{formatDateTime(run.started_at)}</span>
                  </div>
                  <StatusBadge status={run.status} />
                </div>
              ))}
              <Link href="/sync" className="text-xs text-[var(--accent)] hover:underline mt-2 inline-block">
                View all runs
              </Link>
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-4">No sync runs yet</p>
          )}
        </Card>
      </div>

      {/* Data Freshness */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Data Freshness</h2>
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100/70 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-700">Object</th>
              <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-700">Last Sync</th>
              <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-700">Hours Ago</th>
              <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-700">Row Count</th>
              <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-700">Status</th>
            </tr>
          </thead>
          <tbody>
            {(freshness?.data?.objects || []).map((obj, idx) => (
              <tr key={obj.object_name} className={cn("border-t border-slate-100", idx % 2 === 1 && "bg-slate-50/50")}>
                <td className="px-4 py-2.5 font-mono">{obj.object_name}</td>
                <td className="px-4 py-2.5 text-slate-600">
                  {obj.last_sync_at ? formatDateTime(obj.last_sync_at) : "Never"}
                </td>
                <td className="px-4 py-2.5 tabular-nums">{obj.hours_since_sync?.toFixed(1) ?? "\u2014"}</td>
                <td className="px-4 py-2.5 text-right font-mono tabular-nums">{formatNumber(obj.row_count)}</td>
                <td className="px-4 py-2.5">
                  <Badge variant={obj.is_stale ? "danger" : "success"}>
                    {obj.is_stale ? "Stale" : "Fresh"}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

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
  Database,
  Lock,
  BarChart3,
  Zap,
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

  const totalRecords = Object.values(counts).reduce((a, b) => a + (b || 0), 0);

  return (
    <div>
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-[var(--accent-darker)] via-[var(--accent)] to-teal-500 text-white p-6 sm:p-8 mb-8">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMCAyMGgyME0yMCAwdjIwIiBzdHJva2U9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiIHN0cm9rZS13aWR0aD0iMSIvPjwvc3ZnPg==')] opacity-50" />
        <div className="relative z-10">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Sage Finance OS</h1>
          <p className="text-teal-100 mt-1 text-sm sm:text-base max-w-2xl">
            Finance intelligence platform — Sage Intacct extraction, 6-dimension trust scoring, and real-time analytics.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-5">
            <div className="flex items-center gap-2.5 bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2.5">
              <Database size={18} className="text-teal-200 shrink-0" />
              <div>
                <div className="text-lg font-bold leading-tight">{formatNumber(totalRecords)}</div>
                <div className="text-[11px] text-teal-200 uppercase tracking-wide">Records</div>
              </div>
            </div>
            <div className="flex items-center gap-2.5 bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2.5">
              <Lock size={18} className="text-teal-200 shrink-0" />
              <div>
                <div className="text-lg font-bold leading-tight">{latestScorecard ? `${latestScorecard.composite.toFixed(0)}%` : "--"}</div>
                <div className="text-[11px] text-teal-200 uppercase tracking-wide">Trust Score</div>
              </div>
            </div>
            <div className="flex items-center gap-2.5 bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2.5">
              <BarChart3 size={18} className="text-teal-200 shrink-0" />
              <div>
                <div className="text-lg font-bold leading-tight">43</div>
                <div className="text-[11px] text-teal-200 uppercase tracking-wide">API Endpoints</div>
              </div>
            </div>
            <div className="flex items-center gap-2.5 bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2.5">
              <Zap size={18} className="text-teal-200 shrink-0" />
              <div>
                <div className="text-lg font-bold leading-tight">{runs.length > 0 ? "Live" : "Ready"}</div>
                <div className="text-[11px] text-teal-200 uppercase tracking-wide">Pipeline</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <PageHeader
        title="Dashboard"
        actions={
          <div className="text-sm text-[var(--text-secondary)]">
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
      <h2 className="text-lg font-semibold text-[var(--text)] mb-3">Data Freshness</h2>
      <div className="bg-[var(--surface)] rounded-lg border border-[var(--border)] shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-[var(--bg-secondary)] border-b border-[var(--border)]">
            <tr>
              <th className="text-left px-3 py-2.5 sm:px-4 sm:py-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">Object</th>
              <th className="text-left px-3 py-2.5 sm:px-4 sm:py-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] hidden sm:table-cell">Last Sync</th>
              <th className="text-left px-3 py-2.5 sm:px-4 sm:py-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">Hours Ago</th>
              <th className="text-right px-3 py-2.5 sm:px-4 sm:py-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">Rows</th>
              <th className="text-left px-3 py-2.5 sm:px-4 sm:py-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">Status</th>
            </tr>
          </thead>
          <tbody>
            {(freshness?.data?.objects || []).map((obj, idx) => (
              <tr key={obj.object_name} className={cn("border-t border-[var(--border)]", idx % 2 === 1 && "bg-[var(--bg-secondary)]/50")}>
                <td className="px-3 py-2 sm:px-4 sm:py-2.5 font-mono text-xs sm:text-sm">{obj.object_name}</td>
                <td className="px-3 py-2 sm:px-4 sm:py-2.5 text-[var(--text-secondary)] hidden sm:table-cell">
                  {obj.last_sync_at ? formatDateTime(obj.last_sync_at) : "Never"}
                </td>
                <td className="px-3 py-2 sm:px-4 sm:py-2.5 tabular-nums">{obj.hours_since_sync?.toFixed(1) ?? "\u2014"}</td>
                <td className="px-3 py-2 sm:px-4 sm:py-2.5 text-right font-mono tabular-nums">{formatNumber(obj.row_count)}</td>
                <td className="px-3 py-2 sm:px-4 sm:py-2.5">
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
    </div>
  );
}

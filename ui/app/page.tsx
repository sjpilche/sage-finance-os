"use client";

import { useApi } from "@/lib/api/client";

export default function Dashboard() {
  const { data: summary } = useApi<Record<string, number>>("/v1/data/summary");
  const { data: freshness } = useApi<{ last_sync: string | null; objects: any[] }>(
    "/v1/platform/freshness"
  );

  const counts = summary?.data || {};
  const lastSync = freshness?.data?.last_sync;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <div className="text-sm text-slate-500">
          Last sync: {lastSync ? new Date(lastSync).toLocaleString() : "Never"}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card label="GL Entries" value={counts.gl_entry?.toLocaleString() || "0"} />
        <Card label="AP Invoices" value={counts.ap_invoice?.toLocaleString() || "0"} />
        <Card label="AR Invoices" value={counts.ar_invoice?.toLocaleString() || "0"} />
        <Card label="Vendors" value={counts.vendor?.toLocaleString() || "0"} />
        <Card label="Customers" value={counts.customer?.toLocaleString() || "0"} />
        <Card label="Chart of Accounts" value={counts.chart_of_accounts?.toLocaleString() || "0"} />
        <Card label="Trial Balance" value={counts.trial_balance?.toLocaleString() || "0"} />
        <Card label="Budget Lines" value={counts.budget_line?.toLocaleString() || "0"} />
      </div>

      {/* Data Freshness */}
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Data Freshness</h2>
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Object</th>
              <th className="text-left px-4 py-2 font-medium">Last Sync</th>
              <th className="text-left px-4 py-2 font-medium">Hours Ago</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {(freshness?.data?.objects || []).map((obj: any) => (
              <tr key={obj.object_name} className="border-t border-slate-100">
                <td className="px-4 py-2 font-mono">{obj.object_name}</td>
                <td className="px-4 py-2 text-slate-600">
                  {obj.last_sync_at ? new Date(obj.last_sync_at).toLocaleString() : "Never"}
                </td>
                <td className="px-4 py-2">{obj.hours_since_sync ?? "—"}</td>
                <td className="px-4 py-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      obj.is_stale
                        ? "bg-red-100 text-red-700"
                        : "bg-green-100 text-green-700"
                    }`}
                  >
                    {obj.is_stale ? "Stale" : "Fresh"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="text-2xl font-bold text-slate-900 mt-1">{value}</div>
    </div>
  );
}

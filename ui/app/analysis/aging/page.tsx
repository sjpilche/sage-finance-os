"use client";

import { useRouter } from "next/navigation";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { KpiCard } from "@/components/ui/KpiCard";
import { Card } from "@/components/ui/Card";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { AgingBarChart } from "@/components/charts/AgingBarChart";
import { formatCurrency } from "@/lib/utils";
import type { AgingResult, ARAgingByCustomer } from "@/lib/types/analysis";

const customerColumns: Column<ARAgingByCustomer>[] = [
  { key: "customer_name", header: "Customer", sortable: true },
  { key: "customer_code", header: "Code", className: "font-mono text-slate-500" },
  {
    key: "total_balance",
    header: "Outstanding",
    align: "right",
    render: (row) => <span className="font-mono">{formatCurrency(row.total_balance)}</span>,
    sortable: true,
  },
  {
    key: "invoice_count",
    header: "Invoices",
    align: "right",
    sortable: true,
  },
  {
    key: "max_days_outstanding",
    header: "Max Days",
    align: "right",
    render: (row) => (
      <span className={row.max_days_outstanding > 90 ? "text-red-600 font-medium" : ""}>
        {row.max_days_outstanding}
      </span>
    ),
    sortable: true,
  },
];

export default function AgingPage() {
  const router = useRouter();
  const { data: arData, error: arError, isLoading: arLoading } = useApi<AgingResult>("/v1/analysis/aging/ar");
  const { data: apData, error: apError, isLoading: apLoading } = useApi<AgingResult>("/v1/analysis/aging/ap");
  const { data: custData } = useApi<ARAgingByCustomer[]>("/v1/analysis/aging/ar/by-customer?limit=20");

  const isLoading = arLoading || apLoading;
  const error = arError || apError;
  const ar = arData?.data;
  const ap = apData?.data;
  const customers = custData?.data || [];

  return (
    <div>
      <PageHeader title="AR/AP Aging" subtitle="Outstanding receivables and payables by aging bucket" />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {!isLoading && !error && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Total AR Outstanding" value={formatCurrency(ar?.total_amount)} />
            <KpiCard label="AR Invoices" value={String(ar?.total_count ?? 0)} />
            <KpiCard label="Total AP Outstanding" value={formatCurrency(ap?.total_amount)} />
            <KpiCard label="AP Invoices" value={String(ap?.total_count ?? 0)} />
          </div>

          {/* Aging Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              {ar && <AgingBarChart buckets={ar.buckets} title="Accounts Receivable Aging" />}
            </Card>
            <Card>
              {ap && <AgingBarChart buckets={ap.buckets} title="Accounts Payable Aging" />}
            </Card>
          </div>

          {/* Top Customers */}
          <div>
            <h2 className="text-lg font-semibold text-slate-800 mb-3">Top Customers by Outstanding AR</h2>
            <DataTable
              columns={customerColumns}
              data={customers}
              keyField="customer_code"
              emptyMessage="No customer aging data available"
              onRowClick={(row) => router.push(`/data/ar?customer=${encodeURIComponent(row.customer_name)}`)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

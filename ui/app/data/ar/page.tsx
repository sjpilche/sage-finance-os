"use client";

import { useState } from "react";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePagination } from "@/lib/hooks/usePagination";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { PaginatedData } from "@/lib/types/api";
import type { ARInvoice } from "@/lib/types/data";

const statusVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  paid: "success",
  partial: "warning",
  open: "info" as "default",
  void: "danger",
};

const columns: Column<ARInvoice>[] = [
  { key: "invoice_number", header: "Invoice #", className: "font-mono", sortable: true },
  { key: "customer_code", header: "Customer", className: "font-mono", sortable: true },
  { key: "invoice_date", header: "Date", render: (row) => formatDate(row.invoice_date), sortable: true },
  { key: "due_date", header: "Due", render: (row) => formatDate(row.due_date) },
  { key: "total_amount", header: "Amount", align: "right", render: (row) => <span className="font-mono">{formatCurrency(row.total_amount)}</span>, sortable: true },
  { key: "balance", header: "Balance", align: "right", render: (row) => <span className="font-mono font-medium">{formatCurrency(row.balance)}</span>, sortable: true },
  { key: "status", header: "Status", render: (row) => <Badge variant={statusVariant[row.status] || "default"}>{row.status}</Badge> },
];

export default function ARPage() {
  const { offset, limit, nextPage, prevPage, reset } = usePagination(100);
  const [status, setStatus] = useState("");
  const [customer, setCustomer] = useState("");

  const filters = [
    status && `status=${status}`,
    customer && `customer=${customer}`,
  ].filter(Boolean).join("&");

  const { data, error, isLoading } = useApi<PaginatedData<ARInvoice>>(
    `/v1/data/ar?limit=${limit}&offset=${offset}${filters ? `&${filters}` : ""}`
  );

  const result = data?.data;

  return (
    <div>
      <PageHeader title="Accounts Receivable" subtitle={result ? `${result.total.toLocaleString()} invoices` : undefined} />

      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); reset(); }}
          className="px-3 py-1.5 rounded border border-slate-200 text-sm bg-white"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="partial">Partial</option>
          <option value="paid">Paid</option>
          <option value="void">Void</option>
        </select>
        <input
          type="text"
          placeholder="Customer code..."
          value={customer}
          onChange={(e) => { setCustomer(e.target.value); reset(); }}
          className="px-3 py-1.5 rounded border border-slate-200 text-sm w-40"
        />
      </div>

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {result && (
        <>
          <DataTable columns={columns} data={result.rows} keyField="ar_invoice_id" />
          <Pagination offset={offset} limit={limit} total={result.total} onNext={nextPage} onPrev={prevPage} />
        </>
      )}
    </div>
  );
}

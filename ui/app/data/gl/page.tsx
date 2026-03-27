"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePagination } from "@/lib/hooks/usePagination";
import { ExportButton } from "@/components/ui/ExportButton";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { PaginatedData } from "@/lib/types/api";
import type { GLEntry } from "@/lib/types/data";

const columns: Column<GLEntry>[] = [
  { key: "posting_date", header: "Date", render: (row) => formatDate(row.posting_date), sortable: true },
  { key: "document_number", header: "Document", className: "font-mono" },
  { key: "account_number", header: "Account", className: "font-mono", sortable: true },
  { key: "description", header: "Description", className: "max-w-[200px] truncate" },
  { key: "debit_amount", header: "Debit", align: "right", render: (row) => row.debit_amount ? <span className="font-mono">{formatCurrency(row.debit_amount)}</span> : "", sortable: true },
  { key: "credit_amount", header: "Credit", align: "right", render: (row) => row.credit_amount ? <span className="font-mono">{formatCurrency(row.credit_amount)}</span> : "", sortable: true },
  { key: "dimension_1", header: "Dept", render: (row) => row.dimension_1 || "--" },
];

function GLPageContent() {
  const searchParams = useSearchParams();
  const { offset, limit, nextPage, prevPage, reset } = usePagination(100);
  const [account, setAccount] = useState(searchParams.get("account") || "");
  const [dateFrom, setDateFrom] = useState(searchParams.get("date_from") || "");
  const [dateTo, setDateTo] = useState(searchParams.get("date_to") || "");

  const filters = [
    account && `account=${account}`,
    dateFrom && `date_from=${dateFrom}`,
    dateTo && `date_to=${dateTo}`,
  ].filter(Boolean).join("&");

  const { data, error, isLoading } = useApi<PaginatedData<GLEntry>>(
    `/v1/data/gl?limit=${limit}&offset=${offset}${filters ? `&${filters}` : ""}`
  );

  const result = data?.data;

  return (
    <div>
      <PageHeader
        title="General Ledger"
        subtitle={result ? `${result.total.toLocaleString()} entries` : undefined}
        actions={
          <ExportButton
            endpoint={`/v1/data/gl?limit=5000${filters ? `&${filters}` : ""}`}
            filename="gl-export"
          />
        }
      />

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3 mb-4">
        <input
          type="text"
          placeholder="Account number..."
          value={account}
          onChange={(e) => { setAccount(e.target.value); reset(); }}
          className="px-3 py-2.5 rounded-lg border border-[var(--border)] text-sm bg-[var(--surface)] transition-colors duration-150"
        />
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => { setDateFrom(e.target.value); reset(); }}
          className="px-3 py-2.5 rounded-lg border border-[var(--border)] text-sm bg-[var(--surface)] transition-colors duration-150"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => { setDateTo(e.target.value); reset(); }}
          className="px-3 py-2.5 rounded-lg border border-[var(--border)] text-sm bg-[var(--surface)] transition-colors duration-150"
        />
      </div>

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {result && (
        <>
          <DataTable columns={columns} data={result.rows} keyField="gl_entry_id" />
          <Pagination offset={offset} limit={limit} total={result.total} onNext={nextPage} onPrev={prevPage} />
        </>
      )}
    </div>
  );
}

export default function GLPage() {
  return (
    <Suspense>
      <GLPageContent />
    </Suspense>
  );
}

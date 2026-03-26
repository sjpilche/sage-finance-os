"use client";

import { useApi } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePagination } from "@/lib/hooks/usePagination";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { PaginatedData } from "@/lib/types/api";
import type { TrialBalanceRow } from "@/lib/types/data";

const columns: Column<TrialBalanceRow>[] = [
  { key: "account_number", header: "Account", className: "font-mono", sortable: true },
  { key: "account_name", header: "Name", sortable: true },
  { key: "as_of_date", header: "As Of", render: (row) => formatDate(row.as_of_date) },
  { key: "beginning_balance", header: "Beginning", align: "right", render: (row) => <span className="font-mono">{formatCurrency(row.beginning_balance)}</span>, sortable: true },
  { key: "total_debits", header: "Debits", align: "right", render: (row) => <span className="font-mono">{formatCurrency(row.total_debits)}</span> },
  { key: "total_credits", header: "Credits", align: "right", render: (row) => <span className="font-mono">{formatCurrency(row.total_credits)}</span> },
  { key: "ending_balance", header: "Ending", align: "right", render: (row) => <span className="font-mono font-medium">{formatCurrency(row.ending_balance)}</span>, sortable: true },
];

export default function TrialBalancePage() {
  const { offset, limit, nextPage, prevPage } = usePagination(100);

  const { data, error, isLoading } = useApi<PaginatedData<TrialBalanceRow>>(
    `/v1/data/tb?limit=${limit}&offset=${offset}`
  );

  const result = data?.data;

  return (
    <div>
      <PageHeader title="Trial Balance" subtitle={result ? `${result.total.toLocaleString()} rows` : undefined} />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {result && (
        <>
          <DataTable columns={columns} data={result.rows} keyField="tb_id" />
          <Pagination offset={offset} limit={limit} total={result.total} onNext={nextPage} onPrev={prevPage} />
        </>
      )}
    </div>
  );
}

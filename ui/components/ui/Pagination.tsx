"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  onNext: () => void;
  onPrev: () => void;
}

export function Pagination({ offset, limit, total, onNext, onPrev }: PaginationProps) {
  const page = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);
  const from = offset + 1;
  const to = Math.min(offset + limit, total);

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border border-slate-200 rounded-lg mt-2">
      <div className="text-sm text-slate-500">
        Showing {from}–{to} of {total.toLocaleString()}
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onPrev}
          disabled={offset === 0}
          className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-sm text-slate-600 min-w-[80px] text-center">
          Page {page} of {totalPages}
        </span>
        <button
          onClick={onNext}
          disabled={offset + limit >= total}
          className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

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
    <div className="flex flex-col sm:flex-row items-center justify-between gap-2 px-3 py-2.5 sm:px-4 sm:py-3 bg-[var(--surface)] border border-[var(--border)] rounded-lg shadow-sm mt-2">
      <div className="text-xs sm:text-sm text-[var(--text-secondary)]">
        <span className="font-medium text-[var(--text)]">{from}&ndash;{to}</span> of{" "}
        <span className="font-medium text-[var(--text)]">{total.toLocaleString()}</span>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onPrev}
          disabled={offset === 0}
          className="p-2 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] transition-all duration-150 hover:bg-[var(--bg-hover)] hover:border-[var(--border-strong)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25 focus:ring-offset-1 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-sm font-medium text-[var(--text)] min-w-[80px] text-center">
          Page {page} of {totalPages}
        </span>
        <button
          onClick={onNext}
          disabled={offset + limit >= total}
          className="p-2 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] transition-all duration-150 hover:bg-[var(--bg-hover)] hover:border-[var(--border-strong)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25 focus:ring-offset-1 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

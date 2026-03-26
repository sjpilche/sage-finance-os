"use client";

import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/utils";
import type { StatementLine } from "@/lib/types/semantic";

interface StatementTableProps {
  lines: StatementLine[];
  title?: string;
}

export function StatementTable({ lines, title }: StatementTableProps) {
  const sorted = [...lines].sort((a, b) => a.sort_order - b.sort_order);

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
      {title && (
        <div className="px-5 py-3 border-b border-slate-200 bg-slate-100/70">
          <h3 className="text-sm font-bold uppercase tracking-wide text-slate-800">{title}</h3>
        </div>
      )}
      <table className="w-full text-sm">
        <thead className="bg-slate-100/70 border-b border-slate-200">
          <tr>
            <th className="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-700">Account</th>
            <th className="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-700 w-40">Amount</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((line) => (
            <tr
              key={line.line_key}
              className={cn(
                "border-t border-slate-100",
                line.line_type === "total" && "bg-slate-100/60 border-t-2 border-slate-300",
                line.line_type === "subtotal" && "bg-slate-50/50"
              )}
            >
              <td
                className={cn(
                  "px-5 py-2.5",
                  line.line_type === "header" && "font-bold text-slate-900 pt-5 text-base",
                  line.line_type === "detail" && "pl-10 text-slate-600",
                  line.line_type === "subtotal" && "pl-7 font-semibold text-slate-700",
                  line.line_type === "total" && "font-bold text-slate-900"
                )}
              >
                {line.display_name}
              </td>
              <td
                className={cn(
                  "px-5 py-2.5 text-right font-mono tabular-nums",
                  line.line_type === "header" && "text-transparent",
                  line.line_type === "detail" && "text-slate-600",
                  line.line_type === "subtotal" && "font-semibold text-slate-700",
                  line.line_type === "total" && "font-bold text-slate-900",
                  line.amount < 0 && line.line_type !== "header" && "text-red-600"
                )}
              >
                {line.line_type === "header" ? "" : formatCurrency(line.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from "recharts";
import type { AgingBucket } from "@/lib/types/analysis";
import { formatCurrency, chartTooltipStyle, chartColors } from "@/lib/utils";

interface AgingBarChartProps {
  buckets: AgingBucket[];
  title: string;
}

const BUCKET_COLORS = [chartColors.green, chartColors.amber, chartColors.orange, chartColors.red];

export function AgingBarChart({ buckets, title }: AgingBarChartProps) {
  if (!buckets || buckets.length === 0) {
    return (
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] mb-3">{title}</h3>
        <div className="flex items-center justify-center h-[240px] bg-[var(--surface)] rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)]">
          No aging data available
        </div>
      </div>
    );
  }

  const summary = buckets.map((b) => `${b.label}: $${(b.amount / 1000).toFixed(0)}k`).join(", ");

  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-3">{title}</h3>
      <div role="img" aria-label={`${title} bar chart. ${summary}`}>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={buckets} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#475569", fontSize: 11 }}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <YAxis
            tick={{ fill: "#475569", fontSize: 11 }}
            axisLine={{ stroke: "#e2e8f0" }}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip
            formatter={(value: number) => [formatCurrency(value), "Amount"]}
            contentStyle={chartTooltipStyle}
          />
          <Bar dataKey="amount" radius={[4, 4, 0, 0]} animationDuration={600}>
            <LabelList dataKey="amount" position="top" formatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} style={{ fill: "#475569", fontSize: 11, fontWeight: 600 }} />
            {buckets.map((_, i) => (
              <Cell key={i} fill={BUCKET_COLORS[i] || BUCKET_COLORS[3]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}

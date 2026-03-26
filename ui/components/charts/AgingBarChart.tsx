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
} from "recharts";
import type { AgingBucket } from "@/lib/types/analysis";
import { formatCurrency } from "@/lib/utils";

interface AgingBarChartProps {
  buckets: AgingBucket[];
  title: string;
}

const BUCKET_COLORS = ["#16a34a", "#eab308", "#f97316", "#dc2626"];

export function AgingBarChart({ buckets, title }: AgingBarChartProps) {
  return (
    <div>
      <h3 className="text-sm font-medium text-slate-600 mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={buckets} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#64748b", fontSize: 11 }}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 11 }}
            axisLine={{ stroke: "#e2e8f0" }}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip
            formatter={(value: number) => [formatCurrency(value), "Amount"]}
            contentStyle={{
              background: "#fff",
              border: "1px solid #e2e8f0",
              borderRadius: "6px",
              fontSize: "12px",
            }}
          />
          <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
            {buckets.map((_, i) => (
              <Cell key={i} fill={BUCKET_COLORS[i] || BUCKET_COLORS[3]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

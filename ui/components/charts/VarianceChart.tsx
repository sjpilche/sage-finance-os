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
  ReferenceLine,
} from "recharts";
import type { VarianceDetail } from "@/lib/types/analysis";
import { formatCurrency } from "@/lib/utils";

interface VarianceChartProps {
  details: VarianceDetail[];
  maxItems?: number;
}

export function VarianceChart({ details, maxItems = 15 }: VarianceChartProps) {
  const flagged = details
    .filter((d) => d.is_flagged)
    .sort((a, b) => Math.abs(b.variance) - Math.abs(a.variance))
    .slice(0, maxItems);

  if (flagged.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, flagged.length * 32 + 40)}>
      <BarChart data={flagged} layout="vertical" margin={{ top: 5, right: 20, left: 120, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: "#64748b", fontSize: 11 }}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <YAxis
          type="category"
          dataKey="account_name"
          tick={{ fill: "#64748b", fontSize: 11 }}
          width={110}
        />
        <Tooltip
          formatter={(value: number) => [formatCurrency(value), "Variance"]}
          contentStyle={{
            background: "#fff",
            border: "1px solid #e2e8f0",
            borderRadius: "6px",
            fontSize: "12px",
          }}
        />
        <ReferenceLine x={0} stroke="#94a3b8" />
        <Bar dataKey="variance" radius={[0, 4, 4, 0]}>
          {flagged.map((d, i) => (
            <Cell
              key={i}
              fill={d.direction === "favorable" ? "#16a34a" : "#dc2626"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

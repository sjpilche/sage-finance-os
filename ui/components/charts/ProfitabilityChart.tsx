"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { ProfitabilitySegment } from "@/lib/types/analysis";
import { formatCurrency } from "@/lib/utils";

interface ProfitabilityChartProps {
  segments: ProfitabilitySegment[];
}

export function ProfitabilityChart({ segments }: ProfitabilityChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={segments} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="dimension_value"
          tick={{ fill: "#64748b", fontSize: 11 }}
          axisLine={{ stroke: "#e2e8f0" }}
        />
        <YAxis
          tick={{ fill: "#64748b", fontSize: 11 }}
          axisLine={{ stroke: "#e2e8f0" }}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            formatCurrency(value),
            name === "revenue" ? "Revenue" : name === "expenses" ? "Expenses" : "Net Income",
          ]}
          contentStyle={{
            background: "#fff",
            border: "1px solid #e2e8f0",
            borderRadius: "6px",
            fontSize: "12px",
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: "12px" }}
          formatter={(value) =>
            value === "revenue" ? "Revenue" : value === "expenses" ? "Expenses" : "Net Income"
          }
        />
        <Bar dataKey="revenue" fill="#0f7173" radius={[4, 4, 0, 0]} />
        <Bar dataKey="expenses" fill="#dc2626" radius={[4, 4, 0, 0]} />
        <Bar dataKey="net_income" fill="#16a34a" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

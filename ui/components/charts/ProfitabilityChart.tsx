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
import { formatCurrency, chartTooltipStyle, chartColors } from "@/lib/utils";

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
          tick={{ fill: "#475569", fontSize: 11 }}
          axisLine={{ stroke: "#e2e8f0" }}
        />
        <YAxis
          tick={{ fill: "#475569", fontSize: 11 }}
          axisLine={{ stroke: "#e2e8f0" }}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            formatCurrency(value),
            name === "revenue" ? "Revenue" : name === "expenses" ? "Expenses" : "Net Income",
          ]}
          contentStyle={chartTooltipStyle}
        />
        <Legend
          wrapperStyle={{ fontSize: "12px" }}
          formatter={(value) =>
            value === "revenue" ? "Revenue" : value === "expenses" ? "Expenses" : "Net Income"
          }
        />
        <Bar dataKey="revenue" fill={chartColors.teal} radius={[4, 4, 0, 0]} animationDuration={600} />
        <Bar dataKey="expenses" fill={chartColors.red} radius={[4, 4, 0, 0]} animationDuration={600} />
        <Bar dataKey="net_income" fill={chartColors.green} radius={[4, 4, 0, 0]} animationDuration={600} />
      </BarChart>
    </ResponsiveContainer>
  );
}

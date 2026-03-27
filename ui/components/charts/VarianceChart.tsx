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
  LabelList,
} from "recharts";
import type { VarianceDetail } from "@/lib/types/analysis";
import { formatCurrency, chartTooltipStyle, chartColors } from "@/lib/utils";

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

  const favorable = flagged.filter((d) => d.direction === "favorable").length;
  const unfavorable = flagged.length - favorable;

  return (
    <div role="img" aria-label={`Variance chart showing ${flagged.length} flagged accounts: ${favorable} favorable, ${unfavorable} unfavorable`}>
    <ResponsiveContainer width="100%" height={Math.max(200, flagged.length * 32 + 40)}>
      <BarChart data={flagged} layout="vertical" margin={{ top: 5, right: 20, left: 120, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: "#475569", fontSize: 11 }}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <YAxis
          type="category"
          dataKey="account_name"
          tick={{ fill: "#475569", fontSize: 11 }}
          width={110}
        />
        <Tooltip
          formatter={(value: number) => [formatCurrency(value), "Variance"]}
          contentStyle={chartTooltipStyle}
        />
        <ReferenceLine x={0} stroke="#94a3b8" />
        <Bar dataKey="variance" radius={[0, 4, 4, 0]} animationDuration={600}>
          <LabelList dataKey="direction" position="right" style={{ fill: "#475569", fontSize: 10, textTransform: "uppercase" }} />
          {flagged.map((d, i) => (
            <Cell
              key={i}
              fill={d.direction === "favorable" ? chartColors.green : chartColors.red}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
    </div>
  );
}

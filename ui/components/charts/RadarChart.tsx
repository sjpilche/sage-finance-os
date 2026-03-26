"use client";

import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Scorecard } from "@/lib/types/quality";

interface QualityRadarChartProps {
  scorecard: Scorecard;
}

const DIMENSIONS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "completeness", label: "Completeness" },
  { key: "consistency", label: "Consistency" },
  { key: "validity", label: "Validity" },
  { key: "uniqueness", label: "Uniqueness" },
  { key: "timeliness", label: "Timeliness" },
] as const;

export function QualityRadarChart({ scorecard }: QualityRadarChartProps) {
  const data = DIMENSIONS.map((dim) => ({
    dimension: dim.label,
    value: scorecard[dim.key],
    fullMark: 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RechartsRadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fill: "#64748b", fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "#94a3b8", fontSize: 10 }}
        />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(1)}%`, "Score"]}
          contentStyle={{
            background: "#fff",
            border: "1px solid #e2e8f0",
            borderRadius: "6px",
            fontSize: "12px",
          }}
        />
        <Radar
          dataKey="value"
          stroke="#0f7173"
          fill="#0f7173"
          fillOpacity={0.2}
          strokeWidth={2}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}

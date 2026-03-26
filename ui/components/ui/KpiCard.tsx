import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  delta?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function KpiCard({ label, value, delta, trend, className }: KpiCardProps) {
  return (
    <div className={cn("bg-white rounded-lg border border-slate-200 p-4", className)}>
      <div className="text-sm text-slate-500">{label}</div>
      <div className="text-2xl font-bold text-slate-900 mt-1">{value}</div>
      {delta && (
        <div
          className={cn("text-xs mt-1 font-medium", {
            "text-green-600": trend === "up",
            "text-red-600": trend === "down",
            "text-slate-500": trend === "neutral" || !trend,
          })}
        >
          {delta}
        </div>
      )}
    </div>
  );
}

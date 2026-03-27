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
    <div
      className={cn(
        "bg-[var(--surface)] rounded-lg border border-[var(--border)] p-5",
        "shadow-sm hover:shadow-md transition-shadow duration-200",
        className
      )}
    >
      <div className="text-xs font-medium uppercase tracking-wide text-[var(--text-secondary)]">{label}</div>
      <div className="text-2xl font-bold tracking-tight text-[var(--text)] mt-1.5">{value}</div>
      {delta && (
        <div
          className={cn("text-sm font-semibold mt-1.5", {
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

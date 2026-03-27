import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-slate-200 dark:bg-slate-700",
        className
      )}
      style={style}
    />
  );
}

export function SkeletonKpiCard() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
      <Skeleton className="h-3 w-24 mb-3" />
      <Skeleton className="h-7 w-16" />
    </div>
  );
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3">
      <Skeleton className="h-4 w-32" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-3 w-full" style={{ width: `${85 - i * 10}%` }} />
      ))}
    </div>
  );
}

export function SkeletonTableRow({ cols = 5 }: { cols?: number }) {
  return (
    <tr className="border-t border-slate-100">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-3 w-full" style={{ width: `${60 + Math.random() * 30}%` }} />
        </td>
      ))}
    </tr>
  );
}

export function SkeletonTable({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
      <table className="w-full">
        <thead className="bg-slate-100/70 border-b border-slate-200">
          <tr>
            {Array.from({ length: cols }).map((_, i) => (
              <th key={i} className="px-4 py-3">
                <Skeleton className="h-3 w-20" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <SkeletonTableRow key={i} cols={cols} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SkeletonChart({ height = 240 }: { height?: number }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
      <Skeleton className="h-3 w-32 mb-4" />
      <Skeleton className="w-full rounded-lg" style={{ height }} />
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div>
      <Skeleton className="h-7 w-32 mb-6" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonKpiCard key={i} />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <SkeletonCard lines={4} />
        <SkeletonCard lines={2} />
        <SkeletonCard lines={4} />
      </div>
      <Skeleton className="h-5 w-36 mb-3" />
      <SkeletonTable rows={5} cols={5} />
    </div>
  );
}

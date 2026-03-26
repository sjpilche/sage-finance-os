import { cn } from "@/lib/utils";

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Card({ title, children, className }: CardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-lg border border-slate-200 p-4 sm:p-5",
        "shadow-sm hover:shadow-md transition-shadow duration-200",
        className
      )}
    >
      {title && (
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-3">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}

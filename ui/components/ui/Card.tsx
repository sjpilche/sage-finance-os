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
        "bg-[var(--surface)] rounded-lg border border-[var(--border)] p-4 sm:p-5",
        "shadow-sm hover:shadow-md transition-shadow duration-200",
        className
      )}
    >
      {title && (
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] mb-3">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}

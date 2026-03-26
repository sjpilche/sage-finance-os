import { cn } from "@/lib/utils";

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Card({ title, children, className }: CardProps) {
  return (
    <div className={cn("bg-white rounded-lg border border-slate-200 p-5", className)}>
      {title && <h3 className="text-sm font-medium text-slate-500 mb-3">{title}</h3>}
      {children}
    </div>
  );
}

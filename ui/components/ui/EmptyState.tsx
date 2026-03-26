import { Inbox } from "lucide-react";

interface EmptyStateProps {
  message?: string;
  icon?: React.ReactNode;
}

export function EmptyState({ message = "No data available", icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-slate-400">
      {icon || <Inbox size={40} strokeWidth={1.5} />}
      <p className="mt-3 text-sm">{message}</p>
    </div>
  );
}

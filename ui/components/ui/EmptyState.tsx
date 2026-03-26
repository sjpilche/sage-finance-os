import { Inbox } from "lucide-react";

interface EmptyStateProps {
  message?: string;
  icon?: React.ReactNode;
}

export function EmptyState({ message = "No data available", icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-500">
      <div className="text-slate-300 mb-4">
        {icon || <Inbox size={48} strokeWidth={1.5} />}
      </div>
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}

import { AlertTriangle } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = "Something went wrong", onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-slate-400">
      <AlertTriangle size={36} strokeWidth={1.5} className="text-red-400" />
      <p className="mt-3 text-sm text-red-600">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 px-3 py-1.5 text-sm rounded border border-slate-200 text-slate-600 hover:bg-slate-50"
        >
          Retry
        </button>
      )}
    </div>
  );
}

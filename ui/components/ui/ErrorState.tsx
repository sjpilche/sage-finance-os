import { AlertTriangle } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = "Something went wrong", onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <AlertTriangle size={40} strokeWidth={1.5} className="text-red-500 mb-4" />
      <p className="text-sm font-medium text-red-700 text-center max-w-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25 focus:ring-offset-1"
        >
          Try Again
        </button>
      )}
    </div>
  );
}

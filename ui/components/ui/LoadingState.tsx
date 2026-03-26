import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-500">
      <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
      <p className="mt-3 text-sm font-medium">{message}</p>
    </div>
  );
}

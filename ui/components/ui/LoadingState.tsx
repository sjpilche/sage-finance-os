import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-slate-400">
      <Loader2 size={32} className="animate-spin" />
      <p className="mt-3 text-sm">{message}</p>
    </div>
  );
}

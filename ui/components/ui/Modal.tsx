"use client";

import { useEffect, useRef } from "react";
import { X } from "lucide-react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open) {
      dialog.showModal();
    } else {
      dialog.close();
    }
  }, [open]);

  if (!open) return null;

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="backdrop:bg-black/50 backdrop:backdrop-blur-sm rounded-xl shadow-2xl border border-[var(--border)] bg-[var(--surface)] p-0 max-w-lg w-full animate-[modal-enter_200ms_ease-out]"
    >
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)] bg-[var(--bg-secondary)] rounded-t-xl">
        <h2 className="text-lg font-bold text-[var(--text)]">{title}</h2>
        <button
          onClick={onClose}
          aria-label="Close dialog"
          className="p-1.5 rounded-md hover:bg-slate-200 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25"
        >
          <X size={18} className="text-slate-500" />
        </button>
      </div>
      <div className="p-6">{children}</div>
    </dialog>
  );
}

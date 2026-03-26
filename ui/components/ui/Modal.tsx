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
      className="backdrop:bg-black/40 rounded-lg shadow-xl border border-slate-200 p-0 max-w-lg w-full"
    >
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
        <h2 className="font-semibold text-slate-900">{title}</h2>
        <button onClick={onClose} className="p-1 rounded hover:bg-slate-100">
          <X size={18} className="text-slate-500" />
        </button>
      </div>
      <div className="p-5">{children}</div>
    </dialog>
  );
}

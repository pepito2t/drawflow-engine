import { useEffect } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import type { Toast } from "../lib/toasts";
import { CloseIcon } from "./icons";

export function Toaster({ onOpenModule }: { onOpenModule: (moduleId: string) => void }) {
  const { toasts, dismiss } = useNotificationCenter();
  return (
    <div className="toaster" aria-live="polite">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={dismiss} onOpenModule={onOpenModule} />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onDismiss: (id: number) => void;
  onOpenModule: (moduleId: string) => void;
}

function ToastItem({ toast, onDismiss, onOpenModule }: ToastItemProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, toast.durationMs);
    return () => {
      clearTimeout(timer);
    };
  }, [toast.id, toast.durationMs, onDismiss]);

  const open = () => {
    if (toast.moduleId) {
      onOpenModule(toast.moduleId);
      onDismiss(toast.id);
    }
  };

  return (
    <div className={`toast ${toast.tone}`} role={toast.tone === "error" ? "alert" : "status"}>
      <button type="button" className="toast-body" onClick={open} disabled={!toast.moduleId}>
        <strong>{toast.title}</strong>
        {toast.body && <span>{toast.body}</span>}
      </button>
      <button
        type="button"
        className="icon-button"
        aria-label="Fermer la notification"
        onClick={() => {
          onDismiss(toast.id);
        }}
      >
        <CloseIcon size={14} />
      </button>
    </div>
  );
}

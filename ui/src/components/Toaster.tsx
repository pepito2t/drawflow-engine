import { t } from "../i18n/shell";
import { useEffect } from "react";
import { useCommands } from "../hooks/command-registry";
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
  const { execute } = useCommands();

  useEffect(() => {
    if (toast.durationMs === null) {
      return;
    }
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
      {toast.actions.length > 0 && (
        <div className="toast-actions">
          {toast.actions.map((action) => (
            <button
              key={action.label}
              type="button"
              className={action.primary ? "primary" : undefined}
              onClick={() => {
                if (action.command) {
                  execute(action.command)
                    .then((result) => {
                      if (!result.ok) {
                        console.error(result.error);
                      }
                    })
                    .catch((error: unknown) => {
                      console.error(error);
                    });
                }
                onDismiss(toast.id);
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
      <button
        type="button"
        className="icon-button"
        aria-label={t("toaster.close")}
        onClick={() => {
          onDismiss(toast.id);
        }}
      >
        <CloseIcon size={14} />
      </button>
    </div>
  );
}

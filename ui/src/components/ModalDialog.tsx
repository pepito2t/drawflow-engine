import { useEffect, useRef, type ReactNode } from "react";

interface ModalDialogProps {
  labelledBy: string;
  /** Escape key: the dialog stays open until the owner decides, e.g. after confirming. */
  onCancel: () => void;
  onBackdropClick: () => void;
  children: ReactNode;
}

/** Native modal: the browser traps focus and makes the page behind inert; focus returns on close. */
export function ModalDialog({ labelledBy, onCancel, onBackdropClick, children }: ModalDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog === null) {
      return;
    }
    const previouslyFocused = document.activeElement;
    dialog.showModal();
    return () => {
      dialog.close();
      if (previouslyFocused instanceof HTMLElement && previouslyFocused.isConnected) {
        previouslyFocused.focus();
      }
    };
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="dialog"
      aria-labelledby={labelledBy}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          // Without this the browser closes the dialog on its own after a repeated Escape.
          event.preventDefault();
          onCancel();
        }
      }}
      onCancel={(event) => {
        event.preventDefault();
      }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onBackdropClick();
        }
      }}
    >
      {children}
    </dialog>
  );
}

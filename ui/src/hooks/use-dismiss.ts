import { useEffect, type RefObject } from "react";

/** Closes a popover on Escape or on a click landing outside of it. */
export function useDismiss(
  container: RefObject<HTMLElement | null>,
  isOpen: boolean,
  onDismiss: () => void,
): void {
  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onDismiss();
      }
    };
    const onMouseDown = (event: MouseEvent) => {
      if (event.target instanceof Node && !container.current?.contains(event.target)) {
        onDismiss();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mousedown", onMouseDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mousedown", onMouseDown);
    };
  }, [container, isOpen, onDismiss]);
}

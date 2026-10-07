import { useEffect } from "react";
import { shortcutCommand } from "../lib/shortcuts";
import { useCommands } from "./command-registry";

const OPEN_DIALOG_SELECTOR = "dialog[open]";

/** Keyboard shortcuts run registry commands, exactly like the Stream Dock or the assistant would. */
export function useGlobalShortcuts(): void {
  const { execute } = useCommands();
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const command = shortcutCommand(event);
      // A shortcut must not act on the screen hidden behind a dialog, e.g. reopen the settings.
      if (command === null || isInsideOpenDialog(event.target)) {
        return;
      }
      event.preventDefault();
      execute(command)
        .then((result) => {
          if (!result.ok) {
            console.warn(`Raccourci ${command} sans effet :`, result.error);
          }
        })
        .catch((error: unknown) => {
          console.error(`Raccourci ${command} en échec :`, error);
        });
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [execute]);
}

function isInsideOpenDialog(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest(OPEN_DIALOG_SELECTOR) !== null;
}

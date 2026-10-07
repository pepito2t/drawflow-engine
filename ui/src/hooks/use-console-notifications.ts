import { useEffect } from "react";
import { appEventDraft } from "../lib/console-capture";
import { recordConsoleEntry } from "../lib/tauri/console";
import { useNotificationCenter } from "./notification-center";

/** Every notable app event also lands in the console, next to the engine's own messages. */
export function useConsoleNotifications(): void {
  const { subscribe } = useNotificationCenter();
  useEffect(
    () =>
      subscribe((event) => {
        const draft = appEventDraft(event);
        if (draft) {
          recordConsoleEntry(draft);
        }
      }),
    [subscribe],
  );
}

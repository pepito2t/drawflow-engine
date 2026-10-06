import { t } from "../i18n/shell";
import { useEffect } from "react";
import { shouldNotify } from "../lib/notification-rule";
import { readNotificationThreshold } from "../lib/settings";
import { getSettings } from "../lib/tauri/engine";
import { isWindowFocused, notify } from "../lib/tauri/notification";
import { useNotificationCenter } from "./notification-center";

const NOTIFIED_OUTCOMES = new Set(["succeeded", "failed"]);

/** Mirrors long or background run results as operating-system notifications. */
export function useSystemNotifications(): void {
  const { subscribe } = useNotificationCenter();

  useEffect(
    () =>
      subscribe((event) => {
        if (event.type !== "runFinished" || !NOTIFIED_OUTCOMES.has(event.outcome)) {
          return;
        }
        const title =
          event.outcome === "succeeded"
            ? t("run.succeededTitle", { module: event.moduleName })
            : t("run.failedTitle", { module: event.moduleName });
        notifyWhenRelevant(event.durationMs, title, event.message);
      }),
    [subscribe],
  );
}

function notifyWhenRelevant(durationMs: number, title: string, body: string): void {
  Promise.all([getSettings().then(readNotificationThreshold), isWindowFocused()])
    .then(async ([threshold, focused]) => {
      if (shouldNotify(durationMs, threshold, focused)) {
        await notify(title, body);
      }
    })
    .catch((error: unknown) => {
      console.error("Notification de fin de traitement impossible :", error);
    });
}

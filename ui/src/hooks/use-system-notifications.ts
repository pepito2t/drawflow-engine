import { t } from "../i18n/shell";
import { useEffect } from "react";
import { shouldNotify } from "../lib/notification-rule";
import { DEFAULT_NOTIFICATION_THRESHOLD_SECONDS, readNotificationThreshold } from "../lib/settings";
import { isWindowFocused, notify } from "../lib/tauri/notification";
import { useNotificationCenter } from "./notification-center";
import { useSettingsFeed } from "./settings-feed";

const NOTIFIED_OUTCOMES = new Set(["succeeded", "failed"]);

/** Mirrors long or background run results as operating-system notifications. */
export function useSystemNotifications(): void {
  const { subscribe } = useNotificationCenter();
  const { latest } = useSettingsFeed();

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
        notifyWhenRelevant(event.durationMs, notificationThreshold(latest()), title, event.message);
      }),
    [subscribe, latest],
  );
}

function notificationThreshold(rawSettings: string | null): number {
  if (rawSettings === null) {
    return DEFAULT_NOTIFICATION_THRESHOLD_SECONDS;
  }
  try {
    return readNotificationThreshold(rawSettings);
  } catch (error: unknown) {
    console.warn("Seuil de notification illisible, valeur par défaut :", error);
    return DEFAULT_NOTIFICATION_THRESHOLD_SECONDS;
  }
}

function notifyWhenRelevant(
  durationMs: number,
  threshold: number,
  title: string,
  body: string,
): void {
  isWindowFocused()
    .then(async (focused) => {
      if (shouldNotify(durationMs, threshold, focused)) {
        await notify(title, body);
      }
    })
    .catch((error: unknown) => {
      console.error("Notification de fin de traitement impossible :", error);
    });
}

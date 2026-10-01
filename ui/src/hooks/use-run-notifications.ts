import { useEffect, useRef } from "react";
import type { CatalogModule } from "../lib/catalog";
import { describeOutcome, shouldNotify } from "../lib/notification-rule";
import type { RunStatus } from "../lib/run-state";
import type { RunsState } from "../lib/runs-store";
import { readNotificationThreshold } from "../lib/settings";
import { getSettings } from "../lib/tauri/engine";
import { isWindowFocused, notify } from "../lib/tauri/notification";

interface Observed {
  status: RunStatus;
  startedAt: number;
}

export function useRunNotifications(state: RunsState, modules: CatalogModule[]): void {
  const observed = useRef(new Map<string, Observed>());

  useEffect(() => {
    const now = Date.now();
    for (const [moduleId, entry] of Object.entries(state)) {
      const previous = observed.current.get(moduleId);
      const status = entry.run.status;
      if (status === "running" && previous?.status !== "running") {
        observed.current.set(moduleId, { status, startedAt: now });
        continue;
      }
      if (previous?.status === "running" && status !== "running") {
        const name = modules.find((module) => module.manifest.id === moduleId)?.manifest.name;
        const outcome = describeOutcome(name ?? moduleId, entry.run);
        if (outcome) {
          notifyWhenRelevant(now - previous.startedAt, outcome.title, outcome.body);
        }
      }
      observed.current.set(moduleId, { status, startedAt: previous?.startedAt ?? now });
    }
  }, [state, modules]);
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

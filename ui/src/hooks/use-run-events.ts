import { t } from "../i18n/shell";
import { useEffect, useRef } from "react";
import type { RunOutcome } from "../lib/app-events";
import type { CatalogModule } from "../lib/catalog";
import { describeOutcome } from "../lib/notification-rule";
import type { RunStatus } from "../lib/run-state";
import type { RunsState } from "../lib/runs-store";
import { useNotificationCenter } from "./notification-center";

interface Observed {
  status: RunStatus;
  startedAt: number;
  progress: number | null;
}

const OUTCOMES: Partial<Record<RunStatus, RunOutcome>> = {
  succeeded: "succeeded",
  failed: "failed",
  cancelled: "cancelled",
};

/** Turns run state transitions into runStarted / runFinished events. */
export function useRunEvents(state: RunsState, modules: CatalogModule[]): void {
  const { publish } = useNotificationCenter();
  const observed = useRef(new Map<string, Observed>());

  useEffect(() => {
    const now = Date.now();
    for (const [moduleId, entry] of Object.entries(state)) {
      const previous = observed.current.get(moduleId);
      const status = entry.run.status;
      const moduleName =
        modules.find((module) => module.manifest.id === moduleId)?.manifest.name ?? moduleId;
      if (status === "running" && previous?.status !== "running") {
        observed.current.set(moduleId, { status, startedAt: now, progress: null });
        publish({ type: "runStarted", moduleId, moduleName });
        continue;
      }
      const progress = entry.run.progress;
      if (status === "running" && progress && progress.current !== previous?.progress) {
        publish({
          type: "runProgress",
          moduleId,
          current: progress.current,
          total: progress.total,
        });
      }
      const outcome = OUTCOMES[status];
      if (previous?.status === "running" && outcome) {
        const message = describeOutcome(moduleName, entry.run)?.body ?? t("run.cancelled");
        publish({
          type: "runFinished",
          moduleId,
          moduleName,
          outcome,
          message,
          durationMs: now - previous.startedAt,
          outputs: entry.run.outputs,
        });
      }
      observed.current.set(moduleId, {
        status,
        startedAt: previous?.startedAt ?? now,
        progress: entry.run.progress?.current ?? null,
      });
    }
  }, [state, modules, publish]);
}

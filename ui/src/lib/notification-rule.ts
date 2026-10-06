import { t } from "../i18n/shell";
import type { RunState } from "./run-state";

const MILLISECONDS_PER_SECOND = 1000;

export interface RunNotification {
  title: string;
  body: string;
}

export function shouldNotify(
  durationMs: number,
  thresholdSeconds: number,
  isWindowFocused: boolean,
): boolean {
  return !isWindowFocused || durationMs >= thresholdSeconds * MILLISECONDS_PER_SECOND;
}

export function describeOutcome(moduleName: string, run: RunState): RunNotification | null {
  switch (run.status) {
    case "succeeded":
      return {
        title: t("run.succeededTitle", { module: moduleName }),
        body: run.summary ?? t("run.finished"),
      };
    case "failed": {
      const firstError = run.log.find((entry) => entry.level === "error");
      return {
        title: t("run.failedTitle", { module: moduleName }),
        body: firstError?.message ?? t("notificationRule.failed"),
      };
    }
    case "idle":
    case "running":
    case "cancelled":
      return null;
  }
}

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
      return { title: `${moduleName} terminé`, body: run.summary ?? "Traitement terminé." };
    case "failed": {
      const firstError = run.log.find((entry) => entry.level === "error");
      return {
        title: `${moduleName} : échec`,
        body: firstError?.message ?? "Le traitement a échoué.",
      };
    }
    case "idle":
    case "running":
    case "cancelled":
      return null;
  }
}

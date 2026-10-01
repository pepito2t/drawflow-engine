export type RunOutcome = "succeeded" | "failed" | "cancelled";

export type AppEvent =
  | { type: "runStarted"; moduleId: string; moduleName: string }
  | {
      type: "runFinished";
      moduleId: string;
      moduleName: string;
      outcome: RunOutcome;
      message: string;
      durationMs: number;
    }
  | { type: "updateAvailable"; version: string }
  | { type: "updateDeferred" }
  | { type: "settingsSaved" }
  | { type: "accessCodeChanged" };

export type AppEventListener = (event: AppEvent) => void;

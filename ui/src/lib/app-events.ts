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
  | { type: "settingsSaved" }
  | { type: "accessCodeChanged" };

export type AppEventListener = (event: AppEvent) => void;

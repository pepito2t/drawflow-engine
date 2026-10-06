export type RunOutcome = "succeeded" | "failed" | "cancelled";

export type AppEvent =
  | { type: "runStarted"; moduleId: string; moduleName: string }
  | { type: "runProgress"; moduleId: string; current: number; total: number }
  | { type: "presetRunRequested"; presetId: string; moduleId: string }
  | { type: "featureRunRequested"; moduleId: string; inputs: Record<string, unknown> }
  | { type: "featureRunIncomplete"; moduleId: string; moduleName: string; missing: string[] }
  | {
      type: "runFinished";
      moduleId: string;
      moduleName: string;
      outcome: RunOutcome;
      message: string;
      durationMs: number;
      outputs: string[];
    }
  | { type: "updateAvailable"; version: string }
  | { type: "updateDeferred" }
  | { type: "settingsSaved" }
  | { type: "presetSaved"; name: string }
  | { type: "templateImported"; name: string }
  | { type: "settingsExported"; target: string }
  | { type: "accessCodeChanged" }
  | { type: "setupNeeded"; missing: number }
  | { type: "mailFetched"; added: number };

export type AppEventListener = (event: AppEvent) => void;

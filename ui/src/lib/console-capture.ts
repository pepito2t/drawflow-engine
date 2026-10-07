import { t } from "../i18n/console";
import type { AppEvent } from "./app-events";
import type { ConsoleDraft, ConsoleSource } from "./console";
import { SUCCESS_EXIT_CODE, type EngineMessage } from "./engine-message";
import { parseEventLine } from "./events";

/** Who started an engine process, so each console line says where it comes from. */
export interface ConsoleOrigin {
  source: ConsoleSource;
  module?: string;
}

type Detail = Pick<ConsoleDraft, "detail">;

const MILLISECONDS_PER_SECOND = 1000;

function detailOf(parts: readonly (string | null | undefined)[]): Detail {
  const detail = parts.filter((part): part is string => Boolean(part)).join("\n");
  return detail ? { detail } : {};
}

/** Progress and table previews are not diagnostics; every other engine message is kept. */
export function engineMessageDrafts(message: EngineMessage, origin: ConsoleOrigin): ConsoleDraft[] {
  switch (message.kind) {
    case "stdout":
      return stdoutDrafts(message.line, origin);
    case "stderr":
      return message.line.trim() ? [{ ...origin, level: "warning", message: message.line }] : [];
    case "exit":
      return [exitDraft(message.code, origin)];
  }
}

function stdoutDrafts(line: string, origin: ConsoleOrigin): ConsoleDraft[] {
  const event = parseEventLine(line);
  if (event === null) {
    // The assistant streams its own event types (text deltas, tool calls): too noisy to keep.
    const isNoise = origin.source === "assistant" || !line.trim();
    return isNoise ? [] : [{ ...origin, level: "debug", message: line }];
  }
  switch (event.type) {
    case "log":
      return [{ ...origin, level: "info", message: event.message }];
    case "warning":
      return [
        {
          ...origin,
          level: "warning",
          message: event.message,
          ...detailOf([event.file, event.location, event.hint]),
        },
      ];
    case "error":
      return [
        {
          ...origin,
          level: "error",
          message: event.message,
          ...detailOf([event.file, event.hint]),
        },
      ];
    case "result":
      return [{ ...origin, level: "info", message: event.summary, ...detailOf(event.outputs) }];
    case "progress":
    case "table":
      return [];
  }
}

function exitDraft(code: number | null, origin: ConsoleOrigin): ConsoleDraft {
  if (code === SUCCESS_EXIT_CODE) {
    return { ...origin, level: "debug", message: t("capture.exitSuccess") };
  }
  if (code === null) {
    return { ...origin, level: "warning", message: t("capture.exitKilled") };
  }
  // The failure itself is already an error, from the engine's error event or the finished run.
  return { ...origin, level: "warning", message: t("capture.exitCode", { code }) };
}

export function invalidMessageDraft(origin: ConsoleOrigin, detail: string): ConsoleDraft {
  return { ...origin, level: "error", message: t("capture.invalidMessage"), detail };
}

/** Notable app events, as published by the notification center; progress ticks are left out. */
export function appEventDraft(event: AppEvent): ConsoleDraft | null {
  const app = { source: "app" } as const;
  switch (event.type) {
    case "runStarted":
      return {
        ...app,
        level: "info",
        module: event.moduleId,
        message: t("capture.runStarted", { name: event.moduleName }),
      };
    case "runProgress":
      return null;
    case "presetRunRequested":
      return {
        ...app,
        level: "debug",
        module: event.moduleId,
        message: t("capture.presetRunRequested"),
      };
    case "featureRunRequested":
    case "formRunRequested":
      return {
        ...app,
        level: "debug",
        module: event.moduleId,
        message: t("capture.featureRunRequested"),
      };
    case "featureRunIncomplete":
      return {
        ...app,
        level: "warning",
        module: event.moduleId,
        message: t("capture.featureRunIncomplete", { name: event.moduleName }),
        ...detailOf(event.missing),
      };
    case "runFinished":
      return runFinishedDraft(event);
    case "updateAvailable":
      return { ...app, level: "info", message: t("capture.updateAvailable", event) };
    case "updateDeferred":
      return { ...app, level: "info", message: t("capture.updateDeferred") };
    case "settingsSaved":
      return { ...app, level: "info", message: t("capture.settingsSaved") };
    case "presetSaved":
      return { ...app, level: "info", message: t("capture.presetSaved", event) };
    case "templateImported":
      return { ...app, level: "info", message: t("capture.templateImported", event) };
    case "settingsExported":
      return { ...app, level: "info", message: t("capture.settingsExported") };
    case "accessCodeChanged":
      return { ...app, level: "info", message: t("capture.accessCodeChanged") };
    case "setupNeeded":
      return {
        ...app,
        level: "warning",
        message: t("capture.setupNeeded", { count: event.missing }),
      };
    case "mailFetched":
      return { ...app, level: "info", message: t("capture.mailFetched", { count: event.added }) };
  }
}

type RunFinished = Extract<AppEvent, { type: "runFinished" }>;

const RUN_OUTCOME_LEVEL = {
  succeeded: "info",
  failed: "error",
  cancelled: "warning",
} as const satisfies Record<RunFinished["outcome"], ConsoleDraft["level"]>;

const RUN_OUTCOME_MESSAGE = {
  succeeded: "capture.runSucceeded",
  failed: "capture.runFailed",
  cancelled: "capture.runCancelled",
} as const;

function runFinishedDraft(event: RunFinished): ConsoleDraft {
  const seconds = (event.durationMs / MILLISECONDS_PER_SECOND).toFixed(1);
  return {
    source: "app",
    level: RUN_OUTCOME_LEVEL[event.outcome],
    module: event.moduleId,
    message: t(RUN_OUTCOME_MESSAGE[event.outcome], { name: event.moduleName }),
    ...detailOf([event.message, t("capture.duration", { seconds }), ...event.outputs]),
  };
}

interface DescribedError {
  message: string;
  detail?: string;
}

export function describeUnknownError(error: unknown): DescribedError {
  if (error instanceof Error) {
    return { message: error.message, ...detailOf([error.stack]) };
  }
  if (typeof error === "string") {
    return { message: error };
  }
  return { message: t("capture.unknownError") };
}

export function uiErrorDraft(error: unknown, componentStack?: string | null): ConsoleDraft {
  const { message, detail } = describeUnknownError(error);
  return {
    source: "app",
    level: "error",
    message: t("capture.uiError", { message }),
    ...detailOf([detail, componentStack]),
  };
}

export function bridgeErrorDraft(command: string, message: string): ConsoleDraft {
  return { source: "bridge", level: "error", module: command, message };
}

export interface EngineFailure {
  message: string;
  hint: string | null;
  file: string | null;
}

export function engineFailureDraft(request: string, failure: EngineFailure): ConsoleDraft {
  return {
    source: "engine",
    level: "error",
    module: request,
    message: failure.message,
    ...detailOf([failure.file, failure.hint]),
  };
}

type ErrorTarget = Pick<Window, "addEventListener" | "removeEventListener">;

/** Errors nobody caught would otherwise vanish in a desktop app without developer tools. */
export function captureGlobalErrors(
  target: ErrorTarget,
  record: (draft: ConsoleDraft) => void,
): () => void {
  const onError = (event: ErrorEvent) => {
    const error: unknown = event.error;
    record(uiErrorDraft(error ?? event.message));
  };
  const onRejection = (event: PromiseRejectionEvent) => {
    const { message, detail } = describeUnknownError(event.reason);
    record({
      source: "app",
      level: "error",
      message: t("capture.unhandledRejection", { message }),
      ...detailOf([detail]),
    });
  };
  target.addEventListener("error", onError);
  target.addEventListener("unhandledrejection", onRejection);
  return () => {
    target.removeEventListener("error", onError);
    target.removeEventListener("unhandledrejection", onRejection);
  };
}

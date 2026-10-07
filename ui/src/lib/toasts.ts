import { plural } from "../i18n";
import { t } from "../i18n/shell";
import type { AppEvent } from "./app-events";
import { COMMANDS, type CommandId } from "./commands";

export type ToastTone = "success" | "info" | "warning" | "error";

export interface ToastAction {
  label: string;
  /** `null` only closes the toast. */
  command: CommandId | null;
  primary: boolean;
}

export interface Toast {
  id: number;
  tone: ToastTone;
  title: string;
  body: string | null;
  moduleId: string | null;
  /** `null` keeps the toast until the user answers. */
  durationMs: number | null;
  actions: ToastAction[];
}

export type ToastSpec = Omit<Toast, "id">;

export interface ToastsState {
  nextId: number;
  toasts: Toast[];
}

export type ToastsAction = { type: "shown"; toast: ToastSpec } | { type: "dismissed"; id: number };

export const MAX_VISIBLE_TOASTS = 4;
export const SHORT_TOAST_MS = 5_000;
export const LONG_TOAST_MS = 10_000;
export const INITIAL_TOASTS: ToastsState = { nextId: 1, toasts: [] };

export function toastsReducer(state: ToastsState, action: ToastsAction): ToastsState {
  switch (action.type) {
    case "shown": {
      const toasts = [...state.toasts, { ...action.toast, id: state.nextId }];
      return { nextId: state.nextId + 1, toasts: evictOldestTimed(toasts) };
    }
    case "dismissed":
      return { ...state, toasts: state.toasts.filter((toast) => toast.id !== action.id) };
  }
}

/** Toasts waiting for an answer, and the one just shown, are never pushed out by passing ones. */
function evictOldestTimed(toasts: Toast[]): Toast[] {
  const kept = [...toasts];
  while (kept.length > MAX_VISIBLE_TOASTS) {
    const newest = kept.length - 1;
    const oldestTimed = kept.findIndex(
      (toast, index) => index < newest && toast.durationMs !== null,
    );
    if (oldestTimed === -1) {
      break;
    }
    kept.splice(oldestTimed, 1);
  }
  return kept;
}

export function toastFor(event: AppEvent): ToastSpec | null {
  switch (event.type) {
    case "runStarted":
    case "runProgress":
    case "presetRunRequested":
    case "featureRunRequested":
      return null;
    case "runFinished":
      return runToast(event);
    case "featureRunIncomplete":
      return {
        tone: "info",
        title: t("toasts.runIncomplete.title", { module: event.moduleName }),
        body: t("toasts.runIncomplete.body", { fields: event.missing.join(", ") }),
        moduleId: event.moduleId,
        durationMs: null,
        actions: [],
      };
    case "updateAvailable":
      return {
        tone: "info",
        title: t("toasts.updateAvailable.title", { version: event.version }),
        body: t("toasts.updateAvailable.body"),
        moduleId: null,
        durationMs: null,
        actions: [
          {
            label: t("toasts.updateAvailable.install"),
            command: COMMANDS.installUpdate,
            primary: true,
          },
          { label: t("toasts.later"), command: null, primary: false },
        ],
      };
    case "updateDeferred":
      return {
        ...plain("warning", t("toasts.updateDeferred.title")),
        body: t("toasts.updateDeferred.body"),
      };
    case "settingsSaved":
      return plain("success", t("toasts.settingsSaved"));
    case "accessCodeChanged":
      return plain("success", t("toasts.accessCodeChanged"));
    case "presetSaved":
      return { ...plain("success", t("toasts.presetSaved")), body: event.name };
    case "templateImported":
      return { ...plain("success", t("toasts.templateImported")), body: event.name };
    case "settingsExported":
      return { ...plain("success", t("toasts.settingsExported")), body: event.target };
    case "mailFetched":
      return {
        ...plain("success", t("toasts.mailFetched.title")),
        body:
          event.added === 0
            ? t("toasts.mailFetched.none")
            : plural(event.added, t("toasts.mailFetched.one"), t("toasts.mailFetched.other")),
      };
    case "setupNeeded":
      return {
        tone: "info",
        title: t("toasts.setupNeeded.title"),
        body: plural(event.missing, t("toasts.setupNeeded.one"), t("toasts.setupNeeded.other")),
        moduleId: null,
        durationMs: null,
        actions: [
          { label: t("toasts.setupNeeded.open"), command: COMMANDS.openSetup, primary: true },
          { label: t("toasts.later"), command: null, primary: false },
        ],
      };
  }
}

function runToast(event: Extract<AppEvent, { type: "runFinished" }>): ToastSpec {
  const base = { body: event.message, moduleId: event.moduleId, actions: [] };
  switch (event.outcome) {
    case "succeeded":
      return {
        ...base,
        tone: "success",
        title: t("run.succeededTitle", { module: event.moduleName }),
        durationMs: SHORT_TOAST_MS,
      };
    case "failed":
      return {
        ...base,
        tone: "error",
        title: t("run.failedTitle", { module: event.moduleName }),
        durationMs: LONG_TOAST_MS,
      };
    case "cancelled":
      return {
        ...base,
        tone: "info",
        title: t("run.cancelledTitle", { module: event.moduleName }),
        durationMs: SHORT_TOAST_MS,
      };
  }
}

function plain(tone: ToastTone, title: string): ToastSpec {
  return { tone, title, body: null, moduleId: null, durationMs: SHORT_TOAST_MS, actions: [] };
}

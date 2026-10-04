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
      return { nextId: state.nextId + 1, toasts: toasts.slice(-MAX_VISIBLE_TOASTS) };
    }
    case "dismissed":
      return { ...state, toasts: state.toasts.filter((toast) => toast.id !== action.id) };
  }
}

export function toastFor(event: AppEvent): ToastSpec | null {
  switch (event.type) {
    case "runStarted":
    case "runProgress":
    case "presetRunRequested":
      return null;
    case "runFinished":
      return runToast(event);
    case "updateAvailable":
      return {
        tone: "info",
        title: `Version ${event.version} disponible`,
        body: "Voulez-vous mettre à jour maintenant ?",
        moduleId: null,
        durationMs: null,
        actions: [
          { label: "Mettre à jour", command: COMMANDS.installUpdate, primary: true },
          { label: "Plus tard", command: null, primary: false },
        ],
      };
    case "updateDeferred":
      return {
        ...plain("warning", "Mise à jour en attente"),
        body: "Elle pourra être installée une fois les traitements en cours terminés.",
      };
    case "settingsSaved":
      return plain("success", "Paramètres enregistrés");
    case "accessCodeChanged":
      return plain("success", "Code d'accès modifié");
    case "presetSaved":
      return { ...plain("success", "Préréglage enregistré"), body: event.name };
    case "templateImported":
      return { ...plain("success", "Modèle importé"), body: event.name };
    case "settingsExported":
      return { ...plain("success", "Paramètres exportés"), body: event.target };
    case "setupNeeded":
      return {
        tone: "info",
        title: "Configurer Drawflow",
        body:
          event.missing > 1
            ? `${String(event.missing)} éléments sont à installer ou à configurer.`
            : "Un élément est à installer ou à configurer.",
        moduleId: null,
        durationMs: null,
        actions: [
          { label: "Configurer", command: COMMANDS.openSetup, primary: true },
          { label: "Plus tard", command: null, primary: false },
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
        title: `${event.moduleName} terminé`,
        durationMs: SHORT_TOAST_MS,
      };
    case "failed":
      return {
        ...base,
        tone: "error",
        title: `${event.moduleName} : échec`,
        durationMs: LONG_TOAST_MS,
      };
    case "cancelled":
      return {
        ...base,
        tone: "info",
        title: `${event.moduleName} annulé`,
        durationMs: SHORT_TOAST_MS,
      };
  }
}

function plain(tone: ToastTone, title: string): ToastSpec {
  return { tone, title, body: null, moduleId: null, durationMs: SHORT_TOAST_MS, actions: [] };
}

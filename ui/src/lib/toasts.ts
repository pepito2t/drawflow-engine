import type { AppEvent } from "./app-events";

export type ToastTone = "success" | "info" | "warning" | "error";

export interface Toast {
  id: number;
  tone: ToastTone;
  title: string;
  body: string | null;
  moduleId: string | null;
  durationMs: number;
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
      return null;
    case "runFinished":
      return runToast(event);
    case "settingsSaved":
      return plain("success", "Paramètres enregistrés");
    case "accessCodeChanged":
      return plain("success", "Code d'accès modifié");
  }
}

function runToast(event: Extract<AppEvent, { type: "runFinished" }>): ToastSpec {
  const base = { body: event.message, moduleId: event.moduleId };
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
  return { tone, title, body: null, moduleId: null, durationMs: SHORT_TOAST_MS };
}

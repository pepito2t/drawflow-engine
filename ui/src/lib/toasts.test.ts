import { describe, expect, it } from "vitest";
import type { AppEvent } from "./app-events";
import {
  INITIAL_TOASTS,
  LONG_TOAST_MS,
  MAX_VISIBLE_TOASTS,
  toastFor,
  toastsReducer,
  type ToastSpec,
} from "./toasts";

const spec = (title: string): ToastSpec => ({
  tone: "info",
  title,
  body: null,
  moduleId: null,
  durationMs: 1000,
  actions: [],
});

const finished = (outcome: "succeeded" | "failed" | "cancelled"): AppEvent => ({
  type: "runFinished",
  moduleId: "dwg-parts",
  moduleName: "Liste de pièces",
  outcome,
  message: "12 pièces",
  durationMs: 3000,
  outputs: [],
});

describe("toastsReducer", () => {
  it("gives each toast a unique id", () => {
    const state = [spec("a"), spec("b")].reduce(
      (current, toast) => toastsReducer(current, { type: "shown", toast }),
      INITIAL_TOASTS,
    );

    expect(state.toasts.map((toast) => toast.id)).toEqual([1, 2]);
  });

  it("keeps only the most recent toasts", () => {
    const titles = ["1", "2", "3", "4", "5"];
    const state = titles.reduce(
      (current, title) => toastsReducer(current, { type: "shown", toast: spec(title) }),
      INITIAL_TOASTS,
    );

    expect(state.toasts).toHaveLength(MAX_VISIBLE_TOASTS);
    expect(state.toasts[0]?.title).toBe("2");
  });

  it("never evicts a toast that waits for an answer", () => {
    const persistent = { ...spec("ask"), durationMs: null };
    const toasts = [spec("1"), persistent, spec("2"), spec("3"), spec("4")];
    const state = toasts.reduce(
      (current, toast) => toastsReducer(current, { type: "shown", toast }),
      INITIAL_TOASTS,
    );

    expect(state.toasts.map((toast) => toast.title)).toEqual(["ask", "2", "3", "4"]);
  });

  it("keeps the toast just shown even when every other one waits for an answer", () => {
    const persistent = (title: string) => ({ ...spec(title), durationMs: null });
    const toasts = [persistent("a"), persistent("b"), persistent("c"), persistent("d"), spec("e")];
    const state = toasts.reduce(
      (current, toast) => toastsReducer(current, { type: "shown", toast }),
      INITIAL_TOASTS,
    );

    expect(state.toasts.map((toast) => toast.title)).toEqual(["a", "b", "c", "d", "e"]);
  });

  it("removes dismissed toasts", () => {
    const shown = toastsReducer(INITIAL_TOASTS, { type: "shown", toast: spec("a") });

    expect(toastsReducer(shown, { type: "dismissed", id: 1 }).toasts).toEqual([]);
  });
});

describe("toastFor", () => {
  it("links run results to their tab", () => {
    expect(toastFor(finished("succeeded"))).toMatchObject({
      tone: "success",
      title: "Liste de pièces terminé",
      body: "12 pièces",
      moduleId: "dwg-parts",
    });
  });

  it("keeps failures on screen longer", () => {
    expect(toastFor(finished("failed"))).toMatchObject({
      tone: "error",
      durationMs: LONG_TOAST_MS,
    });
  });

  it("confirms settings saves", () => {
    expect(toastFor({ type: "settingsSaved" })?.title).toBe("Paramètres enregistrés");
  });

  it("ignores run starts", () => {
    expect(toastFor({ type: "runStarted", moduleId: "a", moduleName: "A" })).toBeNull();
  });

  it("asks before installing an update and stays until answered", () => {
    const toast = toastFor({ type: "updateAvailable", version: "1.2.0" });

    expect(toast).toMatchObject({ title: "Version 1.2.0 disponible", durationMs: null });
    expect(toast?.actions.map((action) => action.command)).toEqual(["update.install", null]);
  });
});

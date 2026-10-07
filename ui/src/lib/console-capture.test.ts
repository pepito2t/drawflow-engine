import { describe, expect, it } from "vitest";
import type { AppEvent } from "./app-events";
import type { ConsoleDraft } from "./console";
import {
  appEventDraft,
  bridgeErrorDraft,
  captureGlobalErrors,
  engineFailureDraft,
  engineMessageDrafts,
  uiErrorDraft,
} from "./console-capture";

const engine = { source: "engine", module: "dwg-parts" } as const;

function stdout(event: Record<string, unknown>) {
  return { kind: "stdout", line: JSON.stringify(event) } as const;
}

describe("engineMessageDrafts", () => {
  it("keeps log, warning, error and result events with their module", () => {
    expect(engineMessageDrafts(stdout({ type: "log", message: "Lecture" }), engine)).toEqual([
      { source: "engine", module: "dwg-parts", level: "info", message: "Lecture" },
    ]);
    const warning = stdout({
      type: "warning",
      message: "Bloc inconnu",
      file: "A.dwg",
      location: "calque 3",
      hint: null,
    });
    expect(engineMessageDrafts(warning, engine)[0]).toMatchObject({
      level: "warning",
      detail: "A.dwg\ncalque 3",
    });
    const error = stdout({ type: "error", message: "Échec", file: null, hint: "Réessayez" });
    expect(engineMessageDrafts(error, engine)[0]).toMatchObject({
      level: "error",
      message: "Échec",
      detail: "Réessayez",
    });
    const result = stdout({ type: "result", summary: "2 fichiers", outputs: ["a.xlsx", "b.xlsx"] });
    expect(engineMessageDrafts(result, engine)[0]).toMatchObject({
      level: "info",
      message: "2 fichiers",
      detail: "a.xlsx\nb.xlsx",
    });
  });

  it("leaves progress out", () => {
    const progress = stdout({ type: "progress", current: 1, total: 2, message: "x" });
    expect(engineMessageDrafts(progress, engine)).toEqual([]);
  });

  it("keeps stray stdout as debug, except the assistant's own stream", () => {
    const stray = { kind: "stdout", line: "DeprecationWarning" } as const;
    expect(engineMessageDrafts(stray, engine)[0]?.level).toBe("debug");
    expect(engineMessageDrafts(stray, { source: "assistant" })).toEqual([]);
    const assistantError = stdout({
      type: "error",
      message: "Modèle absent",
      file: null,
      hint: null,
    });
    expect(engineMessageDrafts(assistantError, { source: "assistant" })[0]?.level).toBe("error");
  });

  it("reports stderr lines and the exit code", () => {
    const stderr = { kind: "stderr", line: "Traceback (most recent call last):" } as const;
    expect(engineMessageDrafts(stderr, engine)[0]?.level).toBe("warning");
    expect(engineMessageDrafts({ kind: "stderr", line: "  " }, engine)).toEqual([]);
    expect(engineMessageDrafts({ kind: "exit", code: 0 }, engine)[0]?.level).toBe("debug");
    const failed = engineMessageDrafts({ kind: "exit", code: 3 }, engine)[0];
    expect(failed?.level).toBe("warning");
    expect(failed?.message).toContain("3");
    expect(engineMessageDrafts({ kind: "exit", code: null }, engine)[0]?.level).toBe("warning");
  });
});

describe("appEventDraft", () => {
  it("logs a failed run as an error with its message, duration and module", () => {
    const event: AppEvent = {
      type: "runFinished",
      moduleId: "pdf-report",
      moduleName: "Rapport",
      outcome: "failed",
      message: "PDF protégé",
      durationMs: 1500,
      outputs: [],
    };
    const draft = appEventDraft(event);
    expect(draft).toMatchObject({ source: "app", level: "error", module: "pdf-report" });
    expect(draft?.detail).toContain("PDF protégé");
    expect(draft?.detail).toContain("1.5");
  });

  it("ignores progress ticks", () => {
    expect(appEventDraft({ type: "runProgress", moduleId: "a", current: 1, total: 2 })).toBeNull();
  });

  it("never carries the run inputs", () => {
    const draft = appEventDraft({
      type: "featureRunRequested",
      moduleId: "a",
      inputs: { secret: "C:\\Clients\\Privé" },
    });
    expect(JSON.stringify(draft)).not.toContain("Privé");
  });

  it("logs a run launched from the form shortcut like any run request", () => {
    expect(appEventDraft({ type: "formRunRequested", moduleId: "a" })).toEqual(
      appEventDraft({ type: "featureRunRequested", moduleId: "a", inputs: {} }),
    );
  });
});

describe("error drafts", () => {
  it("describes bridge and engine failures", () => {
    expect(bridgeErrorDraft("run_module", "Moteur introuvable")).toEqual({
      source: "bridge",
      level: "error",
      module: "run_module",
      message: "Moteur introuvable",
    });
    expect(
      engineFailureDraft("history.list", { message: "Illisible", hint: null, file: "h.json" }),
    ).toMatchObject({ source: "engine", module: "history.list", detail: "h.json" });
  });

  it("keeps the stack and the component stack of UI errors", () => {
    const error = new Error("boom");
    const draft = uiErrorDraft(error, "\n    at Panel");
    expect(draft.message).toContain("boom");
    expect(draft.detail).toContain("at Panel");
  });
});

describe("captureGlobalErrors", () => {
  it("records uncaught errors and rejections until stopped", () => {
    const target = new EventTarget();
    const recorded: ConsoleDraft[] = [];
    const stop = captureGlobalErrors(target, (draft) => {
      recorded.push(draft);
    });
    const error = Object.assign(new Event("error"), { error: new Error("crash"), message: "" });
    target.dispatchEvent(error);
    const rejection = Object.assign(new Event("unhandledrejection"), { reason: "refusé" });
    target.dispatchEvent(rejection);
    stop();
    target.dispatchEvent(error);

    expect(recorded).toHaveLength(2);
    expect(recorded[0]?.message).toContain("crash");
    expect(recorded[1]?.message).toContain("refusé");
  });
});

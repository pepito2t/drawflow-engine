import { describe, expect, it } from "vitest";
import type { EngineMessage } from "./engine-message";
import { INITIAL_RUN_STATE, runReducer, type RunAction, type RunState } from "./run-state";

const stdout = (event: object): RunAction => ({
  type: "message",
  message: { kind: "stdout", line: JSON.stringify(event) },
});
const exit = (code: number | null): RunAction => ({
  type: "message",
  message: { kind: "exit", code } satisfies EngineMessage,
});

function reduce(actions: RunAction[]): RunState {
  return actions.reduce(runReducer, INITIAL_RUN_STATE);
}

describe("runReducer", () => {
  it("tracks progress, logs and results of a successful run", () => {
    const state = reduce([
      { type: "started" },
      stdout({ type: "progress", current: 1, total: 2, message: "Plan 1" }),
      stdout({ type: "log", message: "Bonjour" }),
      stdout({ type: "result", summary: "OK", outputs: ["out.xlsx"] }),
      exit(0),
    ]);

    expect(state.status).toBe("succeeded");
    expect(state.progress?.current).toBe(1);
    expect(state.log.map((entry) => entry.message)).toEqual(["Bonjour"]);
    expect(state.outputs).toEqual(["out.xlsx"]);
  });

  it("fails with the engine error message", () => {
    const state = reduce([
      { type: "started" },
      stdout({ type: "error", message: "Fichier illisible", file: "a.dwg", hint: "Réessayez" }),
      exit(1),
    ]);

    expect(state.status).toBe("failed");
    expect(state.log).toEqual([
      {
        id: 0,
        level: "error",
        message: "Fichier illisible",
        file: "a.dwg",
        location: null,
        hint: "Réessayez",
      },
    ]);
  });

  it("keeps where a warning is and what to do about it", () => {
    const state = reduce([
      { type: "started" },
      stdout({
        type: "warning",
        message: "Champs introuvables : REF.",
        file: "a.pdf",
        location: "cartouche",
        hint: "Vérifiez la zone du cartouche.",
      }),
    ]);

    expect(state.log[0]).toMatchObject({
      level: "warning",
      location: "cartouche",
      hint: "Vérifiez la zone du cartouche.",
    });
  });

  it("adds a generic error when the engine exits abnormally without explanation", () => {
    const state = reduce([{ type: "started" }, exit(3)]);

    expect(state.status).toBe("failed");
    expect(state.log[0]?.message).toContain("code 3");
  });

  it("marks the run cancelled when cancellation was requested", () => {
    const state = reduce([{ type: "started" }, { type: "cancelRequested" }, exit(null)]);

    expect(state.status).toBe("cancelled");
  });

  it("records stderr lines as technical details", () => {
    const state = reduce([
      { type: "started" },
      { type: "message", message: { kind: "stderr", line: "Traceback" } },
    ]);

    expect(state.log[0]).toMatchObject({ level: "detail", message: "Traceback" });
  });

  it("fails when the bridge cannot start the engine", () => {
    const state = reduce([{ type: "started" }, { type: "bridgeFailed", message: "Moteur absent" }]);

    expect(state.status).toBe("failed");
    expect(state.log[0]?.message).toBe("Moteur absent");
  });

  it("resets previous results on a new start", () => {
    const state = reduce([
      { type: "started" },
      stdout({ type: "log", message: "ancien" }),
      exit(0),
      { type: "started" },
    ]);

    expect(state).toEqual({ ...INITIAL_RUN_STATE, status: "running" });
  });
});

import { describe, expect, it } from "vitest";
import type { RunAction } from "./run-state";
import {
  entryFor,
  overallProgress,
  runningModuleIds,
  runsReducer,
  visibleRunIds,
  type RunsAction,
  type RunsState,
} from "./runs-store";

const run = (moduleId: string, action: RunAction): RunsAction => ({
  type: "run",
  moduleId,
  action,
});
const progress = (moduleId: string, current: number, total: number) =>
  run(moduleId, {
    type: "message",
    message: {
      kind: "stdout",
      line: JSON.stringify({ type: "progress", current, total, message: "" }),
    },
  });
const exit = (moduleId: string, code: number) =>
  run(moduleId, { type: "message", message: { kind: "exit", code } });

function reduce(actions: RunsAction[]): RunsState {
  return actions.reduce(runsReducer, {});
}

describe("runsReducer", () => {
  it("tracks several modules independently", () => {
    const state = reduce([
      run("a", { type: "started" }),
      run("b", { type: "started" }),
      exit("a", 0),
    ]);

    expect(runningModuleIds(state)).toEqual(["b"]);
    expect(entryFor(state, "a").run.status).toBe("succeeded");
  });

  it("flags an unseen outcome when a run finishes until acknowledged", () => {
    const finished = reduce([run("a", { type: "started" }), exit("a", 1)]);

    expect(entryFor(finished, "a").unseenOutcome).toBe(true);
    expect(
      entryFor(runsReducer(finished, { type: "acknowledge", moduleId: "a" }), "a").unseenOutcome,
    ).toBe(false);
  });

  it("stores the run id and resets it on a new start", () => {
    const assigned = reduce([
      run("a", { type: "started" }),
      { type: "runIdAssigned", moduleId: "a", runId: "run-1" },
    ]);

    expect(entryFor(assigned, "a").runId).toBe("run-1");
    expect(entryFor(runsReducer(assigned, run("a", { type: "started" })), "a").runId).toBeNull();
  });

  it("returns an empty entry for unknown modules", () => {
    expect(entryFor({}, "x").run.status).toBe("idle");
  });
});

describe("overallProgress", () => {
  it("aggregates progress of running modules", () => {
    const state = reduce([
      run("a", { type: "started" }),
      run("b", { type: "started" }),
      progress("a", 1, 4),
      progress("b", 3, 4),
    ]);

    expect(overallProgress(state)).toBe(0.5);
  });

  it("is null when nothing reports progress", () => {
    expect(overallProgress(reduce([run("a", { type: "started" })]))).toBeNull();
  });
});

describe("visibleRunIds", () => {
  it("lists modules that have run at least once", () => {
    const state = reduce([
      run("a", { type: "started" }),
      exit("a", 0),
      { type: "acknowledge", moduleId: "b" },
    ]);

    expect(visibleRunIds(state)).toEqual(["a"]);
  });
});

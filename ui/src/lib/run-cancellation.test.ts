import { describe, expect, it } from "vitest";
import type { RunAction } from "./run-state";
import { cancellationRequests } from "./run-cancellation";
import { pendingCancellations, runsReducer, type RunsAction, type RunsState } from "./runs-store";

const run = (moduleId: string, action: RunAction): RunsAction => ({
  type: "run",
  moduleId,
  action,
});

function reduce(actions: RunsAction[], state: RunsState = {}): RunsState {
  return actions.reduce(runsReducer, state);
}

describe("cancellationRequests", () => {
  it("cancels only the requested running module, which is then sent to the engine", () => {
    const state = reduce([
      run("a", { type: "started" }),
      run("b", { type: "started" }),
      { type: "runIdAssigned", moduleId: "a", runId: "r1" },
      { type: "runIdAssigned", moduleId: "b", runId: "r2" },
    ]);

    const cancelled = reduce(cancellationRequests(state, ["a"]), state);

    expect(pendingCancellations(cancelled)).toEqual([{ moduleId: "a", runId: "r1" }]);
  });

  it("asks nothing for a module that is idle, unknown or already cancelling", () => {
    const state = reduce([run("a", { type: "started" }), run("a", { type: "cancelRequested" })]);

    expect(cancellationRequests(state, ["a", "unknown"])).toEqual([]);
  });
});

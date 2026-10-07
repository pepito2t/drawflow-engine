import { entryFor, type RunsAction, type RunsState } from "./runs-store";

/** A module that is not running, or already cancelling, has nothing more to cancel. */
export function cancellationRequests(state: RunsState, moduleIds: readonly string[]): RunsAction[] {
  return moduleIds
    .filter((moduleId) => {
      const { run } = entryFor(state, moduleId);
      return run.status === "running" && !run.cancelRequested;
    })
    .map((moduleId) => ({ type: "run", moduleId, action: { type: "cancelRequested" } }));
}

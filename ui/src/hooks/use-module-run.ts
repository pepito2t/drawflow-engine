import { useCallback } from "react";
import type { FormValues } from "../lib/form-schema";
import type { RunState } from "../lib/run-state";
import { entryFor } from "../lib/runs-store";
import { describeBridgeError, runModule } from "../lib/tauri/engine";
import { useRunsSelector, useRunsStore } from "./runs-context";

interface ModuleRun {
  state: RunState;
  start: (inputs: FormValues) => void;
  cancel: () => void;
}

export function useModuleRun(moduleId: string): ModuleRun {
  const { dispatch } = useRunsStore();
  const run = useRunsSelector((state) => entryFor(state, moduleId).run);

  const bridgeFailed = useCallback(
    (message: string) => {
      dispatch({ type: "run", moduleId, action: { type: "bridgeFailed", message } });
    },
    [dispatch, moduleId],
  );

  const start = useCallback(
    (inputs: FormValues) => {
      dispatch({ type: "run", moduleId, action: { type: "started" } });
      runModule(
        moduleId,
        inputs,
        (message) => {
          dispatch({ type: "run", moduleId, action: { type: "message", message } });
        },
        bridgeFailed,
      )
        .then((assignedRunId) => {
          dispatch({ type: "runIdAssigned", moduleId, runId: assignedRunId });
        })
        .catch((error: unknown) => {
          bridgeFailed(describeBridgeError(error));
        });
    },
    [dispatch, moduleId, bridgeFailed],
  );

  const cancel = useCallback(() => {
    if (run.status !== "running" || run.cancelRequested) {
      return;
    }
    dispatch({ type: "run", moduleId, action: { type: "cancelRequested" } });
  }, [dispatch, moduleId, run.status, run.cancelRequested]);

  return { state: run, start, cancel };
}

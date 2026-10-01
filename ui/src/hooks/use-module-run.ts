import { useCallback, useReducer, useRef } from "react";
import type { FormValues } from "../lib/form-schema";
import { INITIAL_RUN_STATE, runReducer, type RunState } from "../lib/run-state";
import { cancelRun, describeBridgeError, runModule } from "../lib/tauri/engine";

interface ModuleRun {
  state: RunState;
  start: (inputs: FormValues) => void;
  cancel: () => void;
}

export function useModuleRun(moduleId: string): ModuleRun {
  const [state, dispatch] = useReducer(runReducer, INITIAL_RUN_STATE);
  const runIdRef = useRef<string | null>(null);

  const start = useCallback(
    (inputs: FormValues) => {
      dispatch({ type: "started" });
      runModule(moduleId, inputs, (message) => {
        dispatch({ type: "message", message });
      })
        .then((runId) => {
          runIdRef.current = runId;
        })
        .catch((error: unknown) => {
          dispatch({ type: "bridgeFailed", message: describeBridgeError(error) });
        });
    },
    [moduleId],
  );

  const cancel = useCallback(() => {
    const runId = runIdRef.current;
    if (runId === null) {
      return;
    }
    dispatch({ type: "cancelRequested" });
    cancelRun(runId).catch((error: unknown) => {
      dispatch({ type: "bridgeFailed", message: describeBridgeError(error) });
    });
  }, []);

  return { state, start, cancel };
}

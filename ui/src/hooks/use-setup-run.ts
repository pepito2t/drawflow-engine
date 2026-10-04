import { useCallback, useReducer } from "react";
import { toReadableError } from "../lib/error-message";
import { setupRunReducer, type EngineSetupAction, type SetupRun } from "../lib/setup";
import { runSetupAction } from "../lib/tauri/setup";

interface SetupRunner {
  run: SetupRun;
  start: (action: EngineSetupAction) => void;
}

export function useSetupRun(onFinished: () => void): SetupRunner {
  const [run, dispatch] = useReducer(setupRunReducer, { status: "idle" });

  const start = useCallback(
    (action: EngineSetupAction) => {
      dispatch({ kind: "started", action });
      runSetupAction(action, (message) => {
        if (message.kind === "stdout") {
          dispatch({ kind: "line", line: message.line });
        } else if (message.kind === "exit") {
          dispatch({ kind: "exit", code: message.code });
          onFinished();
        } else {
          console.warn("Installation :", message.line);
        }
      }).catch((error: unknown) => {
        dispatch({ kind: "failed", error: toReadableError(error) });
      });
    },
    [onFinished],
  );

  return { run, start };
}

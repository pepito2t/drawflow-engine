import { useCallback, useReducer } from "react";
import type { EngineMessage } from "../lib/engine-message";
import { toReadableError } from "../lib/error-message";
import { setupRunReducer, type SetupRun } from "../lib/setup";

export type TaskLauncher = (onMessage: (message: EngineMessage) => void) => Promise<unknown>;

interface SetupRunner {
  run: SetupRun;
  start: (action: string, launch: TaskLauncher) => void;
}

/** One engine task at a time (installation, model download), followed through its NDJSON. */
export function useSetupRun(onFinished: () => void): SetupRunner {
  const [run, dispatch] = useReducer(setupRunReducer, { status: "idle" });

  const start = useCallback(
    (action: string, launch: TaskLauncher) => {
      dispatch({ kind: "started", action });
      launch((message) => {
        if (message.kind === "stdout") {
          dispatch({ kind: "line", line: message.line });
        } else if (message.kind === "exit") {
          dispatch({ kind: "exit", code: message.code });
          onFinished();
        } else {
          console.warn(`${action} :`, message.line);
        }
      }).catch((error: unknown) => {
        dispatch({ kind: "failed", error: toReadableError(error) });
      });
    },
    [onFinished],
  );

  return { run, start };
}

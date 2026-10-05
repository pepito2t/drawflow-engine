import { useEffect } from "react";
import type { SetupRun, SetupScope } from "../lib/setup";
import { useSetupRunsStore, type TaskLauncher } from "./setup-runs-context";

interface SetupRunner {
  run: SetupRun;
  start: (action: string, launch: TaskLauncher) => void;
}

/** One engine task at a time per screen (installation, model download), followed through its NDJSON. */
export function useSetupRun(scope: SetupScope, onFinished: () => void): SetupRunner {
  const { runs, start, subscribe } = useSetupRunsStore();

  useEffect(() => subscribe(scope, onFinished), [subscribe, scope, onFinished]);

  return {
    run: runs[scope],
    start: (action, launch) => {
      start(scope, action, launch);
    },
  };
}

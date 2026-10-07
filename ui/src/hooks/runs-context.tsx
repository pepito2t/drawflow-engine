import {
  createContext,
  use,
  useEffect,
  useReducer,
  useRef,
  type Dispatch,
  type ReactNode,
} from "react";
import {
  pendingCancellations,
  runsReducer,
  type RunsAction,
  type RunsState,
} from "../lib/runs-store";
import { cancelRun, describeBridgeError } from "../lib/tauri/engine";

interface RunsStore {
  state: RunsState;
  dispatch: Dispatch<RunsAction>;
}

const RunsContext = createContext<RunsStore | null>(null);

export function RunsProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(runsReducer, {});
  useCancellationRelay(state, dispatch);
  return <RunsContext value={{ state, dispatch }}>{children}</RunsContext>;
}

/** Sends each requested cancellation to the bridge exactly once, as soon as the run id is known. */
function useCancellationRelay(state: RunsState, dispatch: Dispatch<RunsAction>): void {
  const sent = useRef(new Set<string>());
  useEffect(() => {
    for (const { moduleId, runId } of pendingCancellations(state)) {
      if (sent.current.has(runId)) {
        continue;
      }
      sent.current.add(runId);
      cancelRun(runId).catch((error: unknown) => {
        const message = describeBridgeError(error);
        dispatch({ type: "run", moduleId, action: { type: "bridgeFailed", message } });
      });
    }
  }, [state, dispatch]);
}

export function useRunsStore(): RunsStore {
  const store = use(RunsContext);
  if (store === null) {
    throw new Error("useRunsStore doit être utilisé dans un RunsProvider.");
  }
  return store;
}

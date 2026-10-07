import {
  createContext,
  use,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import {
  createRunsStore,
  pendingCancellations,
  type RunsState,
  type RunsStore,
} from "../lib/runs-store";
import { cancelRun, describeBridgeError } from "../lib/tauri/engine";

const RunsContext = createContext<RunsStore | null>(null);

export function RunsProvider({ children }: { children: ReactNode }) {
  const [store] = useState(() => createRunsStore());
  useCancellationRelay(store);
  return <RunsContext value={store}>{children}</RunsContext>;
}

/** Sends each requested cancellation to the bridge exactly once, as soon as the run id is known. */
function useCancellationRelay(store: RunsStore): void {
  const sent = useRef(new Set<string>());
  useEffect(() => {
    const relay = () => {
      for (const { moduleId, runId } of pendingCancellations(store.getState())) {
        if (sent.current.has(runId)) {
          continue;
        }
        sent.current.add(runId);
        cancelRun(runId).catch((error: unknown) => {
          const message = describeBridgeError(error);
          store.dispatch({ type: "run", moduleId, action: { type: "bridgeFailed", message } });
        });
      }
    };
    relay();
    return store.subscribe(relay);
  }, [store]);
}

/** Stable for the app's lifetime: read the state at call time, never re-renders the caller. */
export function useRunsStore(): RunsStore {
  const store = use(RunsContext);
  if (store === null) {
    throw new Error("useRunsStore doit être utilisé dans un RunsProvider.");
  }
  return store;
}

/** Re-renders the caller only when the selected value changes; select primitives or stored entries. */
export function useRunsSelector<T>(select: (state: RunsState) => T): T {
  const store = useRunsStore();
  return useSyncExternalStore(store.subscribe, () => select(store.getState()));
}

export function useRunsState(): RunsState {
  return useRunsSelector(identity);
}

const identity = (state: RunsState): RunsState => state;

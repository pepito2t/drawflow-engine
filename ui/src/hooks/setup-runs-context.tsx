import {
  createContext,
  use,
  useCallback,
  useMemo,
  useReducer,
  useRef,
  type ReactNode,
} from "react";
import type { EngineMessageHandler, InvalidMessageHandler } from "../lib/engine-message";
import { toReadableError } from "../lib/error-message";
import { IDLE_SETUP_RUNS, setupRunsReducer, type SetupRuns, type SetupScope } from "../lib/setup";

export type TaskLauncher = (
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
) => Promise<unknown>;

interface SetupRunsStore {
  runs: SetupRuns;
  start: (scope: SetupScope, action: string, launch: TaskLauncher) => void;
  /** Called when the scope's task ends, if its screen is still open; returns the unsubscribe. */
  subscribe: (scope: SetupScope, onFinished: () => void) => () => void;
}

const SetupRunsContext = createContext<SetupRunsStore | null>(null);

/** Installations and model downloads outlive their screen: leaving it must not lose the loader. */
export function SetupRunsProvider({ children }: { children: ReactNode }) {
  const [runs, dispatch] = useReducer(setupRunsReducer, IDLE_SETUP_RUNS);
  const listeners = useRef(new Map<SetupScope, () => void>());

  const subscribe = useCallback((scope: SetupScope, onFinished: () => void) => {
    listeners.current.set(scope, onFinished);
    return () => {
      if (listeners.current.get(scope) === onFinished) {
        listeners.current.delete(scope);
      }
    };
  }, []);

  const start = useCallback((scope: SetupScope, action: string, launch: TaskLauncher) => {
    dispatch({ scope, message: { kind: "started", action } });
    const fail = (error: unknown) => {
      dispatch({ scope, message: { kind: "failed", error: toReadableError(error) } });
    };
    launch((message) => {
      if (message.kind === "stdout") {
        dispatch({ scope, message: { kind: "line", line: message.line } });
      } else if (message.kind === "exit") {
        dispatch({ scope, message: { kind: "exit", code: message.code } });
        listeners.current.get(scope)?.();
      } else {
        console.warn(`${action} :`, message.line);
      }
    }, fail).catch(fail);
  }, []);

  const store = useMemo(() => ({ runs, start, subscribe }), [runs, start, subscribe]);
  return <SetupRunsContext value={store}>{children}</SetupRunsContext>;
}

export function useSetupRunsStore(): SetupRunsStore {
  const store = use(SetupRunsContext);
  if (store === null) {
    throw new Error("useSetupRunsStore doit être utilisé dans un SetupRunsProvider.");
  }
  return store;
}

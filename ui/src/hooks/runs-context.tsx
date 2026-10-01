import { createContext, use, useReducer, type Dispatch, type ReactNode } from "react";
import { runsReducer, type RunsAction, type RunsState } from "../lib/runs-store";

interface RunsStore {
  state: RunsState;
  dispatch: Dispatch<RunsAction>;
}

const RunsContext = createContext<RunsStore | null>(null);

export function RunsProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(runsReducer, {});
  return <RunsContext value={{ state, dispatch }}>{children}</RunsContext>;
}

export function useRunsStore(): RunsStore {
  const store = use(RunsContext);
  if (store === null) {
    throw new Error("useRunsStore doit être utilisé dans un RunsProvider.");
  }
  return store;
}

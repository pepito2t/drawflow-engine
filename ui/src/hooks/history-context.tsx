import { createContext, use, useEffect, useMemo, type ReactNode } from "react";
import type { HistoryEntry } from "../lib/history";
import { listHistory } from "../lib/tauri/history";
import { useNotificationCenter } from "./notification-center";
import { useRetryablePromise } from "./use-retryable-promise";

interface HistoryLoad {
  id: number;
  promise: Promise<HistoryEntry[]>;
  reload: () => void;
}

const HistoryContext = createContext<HistoryLoad | null>(null);

/** One history read shared by every panel, refreshed once per finished run. */
export function HistoryProvider({ children }: { children: ReactNode }) {
  const { id, promise, retry } = useRetryablePromise(listHistory);
  const { subscribe } = useNotificationCenter();
  useEffect(
    () =>
      subscribe((event) => {
        if (event.type === "runFinished") {
          retry();
        }
      }),
    [subscribe, retry],
  );
  const history = useMemo(() => ({ id, promise, reload: retry }), [id, promise, retry]);
  return <HistoryContext value={history}>{children}</HistoryContext>;
}

export function useHistory(): HistoryLoad {
  const history = use(HistoryContext);
  if (history === null) {
    throw new Error("useHistory doit être utilisé dans un HistoryProvider.");
  }
  return history;
}

import {
  createContext,
  use,
  useCallback,
  useMemo,
  useReducer,
  useRef,
  type ReactNode,
} from "react";
import type { AppEvent, AppEventListener } from "../lib/app-events";
import { INITIAL_TOASTS, toastFor, toastsReducer, type Toast } from "../lib/toasts";

interface NotificationCenter {
  publish: (event: AppEvent) => void;
  subscribe: (listener: AppEventListener) => () => void;
  toasts: Toast[];
  dismiss: (id: number) => void;
}

const NotificationContext = createContext<NotificationCenter | null>(null);

/** Single event stream for toasts, system notifications and external integrations. */
export function NotificationProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(toastsReducer, INITIAL_TOASTS);
  const listeners = useRef(new Set<AppEventListener>());

  const publish = useCallback((event: AppEvent) => {
    const toast = toastFor(event);
    if (toast) {
      dispatch({ type: "shown", toast });
    }
    for (const listener of listeners.current) {
      listener(event);
    }
  }, []);

  const subscribe = useCallback((listener: AppEventListener) => {
    listeners.current.add(listener);
    return () => {
      listeners.current.delete(listener);
    };
  }, []);

  const dismiss = useCallback((id: number) => {
    dispatch({ type: "dismissed", id });
  }, []);

  const center = useMemo(
    () => ({ publish, subscribe, toasts: state.toasts, dismiss }),
    [publish, subscribe, state.toasts, dismiss],
  );
  return <NotificationContext value={center}>{children}</NotificationContext>;
}

export function useNotificationCenter(): NotificationCenter {
  const center = use(NotificationContext);
  if (center === null) {
    throw new Error("useNotificationCenter doit être utilisé dans un NotificationProvider.");
  }
  return center;
}

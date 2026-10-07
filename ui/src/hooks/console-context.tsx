import {
  createContext,
  use,
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  type Dispatch,
  type ReactNode,
} from "react";
import { describeOs, formatForSupport, unseenErrorCount, type ConsoleEntry } from "../lib/console";
import {
  consoleReducer,
  INITIAL_CONSOLE_STATE,
  type ConsoleAction,
  type ConsoleState,
} from "../lib/console-store";
import { getAppVersion } from "../lib/tauri/app";
import {
  clearConsole,
  copyToClipboard,
  listConsoleEntries,
  listenToConsole,
  openConsoleWindow,
} from "../lib/tauri/console";
import { describeBridgeError } from "../lib/tauri/engine";

/** Engine runs can log hundreds of lines a second: entries are rendered in small batches. */
const FLUSH_DELAY_MS = 100;
const UNKNOWN_VERSION = "?";

interface ConsoleFeed {
  state: ConsoleState;
  dispatch: Dispatch<ConsoleAction>;
}

/** Subscribes before loading the buffer, so no entry falls between the two; ids deduplicate. */
export function useConsoleFeed(): ConsoleFeed {
  const [state, dispatch] = useReducer(consoleReducer, INITIAL_CONSOLE_STATE);
  const pending = useRef<ConsoleEntry[]>([]);
  const flushTimer = useRef<number | null>(null);

  useEffect(() => {
    let isCancelled = false;
    const isActive = () => !isCancelled;
    let stopListening: (() => void) | null = null;
    const flush = () => {
      flushTimer.current = null;
      const entries = pending.current;
      pending.current = [];
      dispatch({ type: "received", entries });
    };
    const onEntry = (entry: ConsoleEntry) => {
      pending.current.push(entry);
      flushTimer.current ??= window.setTimeout(flush, FLUSH_DELAY_MS);
    };
    const onInvalid = (error: unknown) => {
      console.error("Entrée de console invalide :", error);
    };
    const onCleared = () => {
      dispatch({ type: "cleared" });
    };
    listenToConsole({ onEntry, onCleared, onInvalid })
      .then(async (unlisten) => {
        if (!isActive()) {
          unlisten();
          return;
        }
        stopListening = unlisten;
        const entries = await listConsoleEntries();
        if (isActive()) {
          dispatch({ type: "received", entries });
        }
      })
      .catch((error: unknown) => {
        if (isActive()) {
          dispatch({ type: "loadFailed", message: describeBridgeError(error) });
        }
      });
    return () => {
      isCancelled = true;
      stopListening?.();
      if (flushTimer.current !== null) {
        window.clearTimeout(flushTimer.current);
        flushTimer.current = null;
      }
    };
  }, []);

  return { state, dispatch };
}

let appVersion: Promise<string> | null = null;

function cachedAppVersion(): Promise<string> {
  appVersion ??= getAppVersion().catch((error: unknown) => {
    console.error("Version de l'application indisponible :", error);
    return UNKNOWN_VERSION;
  });
  return appVersion;
}

/** Text ready to paste into an email to the support, with the version and system first. */
export async function copyForSupport(entries: readonly ConsoleEntry[]): Promise<void> {
  const version = await cachedAppVersion();
  const os = describeOs(navigator.userAgent);
  await copyToClipboard(formatForSupport(entries, { version, os, date: new Date() }));
}

interface ConsoleContextValue {
  entries: ConsoleEntry[];
  loadError: string | null;
  isPanelOpen: boolean;
  unseenErrors: number;
  togglePanel: () => void;
  closePanel: () => void;
  detach: () => Promise<void>;
  clear: () => Promise<void>;
}

const ConsoleContext = createContext<ConsoleContextValue | null>(null);

export function ConsoleProvider({ children }: { children: ReactNode }) {
  const { state, dispatch } = useConsoleFeed();

  const togglePanel = useCallback(() => {
    dispatch({ type: "panelToggled" });
  }, [dispatch]);
  const closePanel = useCallback(() => {
    dispatch({ type: "panelClosed" });
  }, [dispatch]);
  const detach = useCallback(async () => {
    await openConsoleWindow();
    dispatch({ type: "detached" });
  }, [dispatch]);

  const value = useMemo(
    () => ({
      entries: state.entries,
      loadError: state.loadError,
      isPanelOpen: state.isPanelOpen,
      unseenErrors: unseenErrorCount(state.entries, state.lastSeenId),
      togglePanel,
      closePanel,
      detach,
      clear: clearConsole,
    }),
    [state, togglePanel, closePanel, detach],
  );
  return <ConsoleContext value={value}>{children}</ConsoleContext>;
}

export function useConsole(): ConsoleContextValue {
  const value = use(ConsoleContext);
  if (value === null) {
    throw new Error("useConsole doit être utilisé dans un ConsoleProvider.");
  }
  return value;
}

/** `null` before unlocking: the lock screen shares the status bar but has no console. */
export function useOptionalConsole(): ConsoleContextValue | null {
  return use(ConsoleContext);
}

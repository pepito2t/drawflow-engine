import {
  createContext,
  Suspense,
  use,
  useCallback,
  useEffect,
  useReducer,
  useRef,
  type ReactNode,
} from "react";
import { COMMANDS } from "../lib/commands";
import { describeBridgeError } from "../lib/tauri/engine";
import { findUpdate, isUpdaterConfigured, type AvailableUpdate } from "../lib/tauri/updater";
import { updateReducer, type UpdateState } from "../lib/update-state";
import { useCommand } from "./command-registry";
import { useNotificationCenter } from "./notification-center";

interface StartupCheck {
  state: UpdateState;
  update: AvailableUpdate | null;
}

interface UpdateCenter {
  state: UpdateState;
  install: () => void;
}

const UpdateContext = createContext<UpdateCenter | null>(null);

const startupCheckPromise: Promise<StartupCheck> = checkAtStartup();

async function checkAtStartup(): Promise<StartupCheck> {
  try {
    if (!(await isUpdaterConfigured())) {
      return { state: { status: "unconfigured" }, update: null };
    }
    const update = await findUpdate();
    return update
      ? { state: { status: "available", version: update.version }, update }
      : { state: { status: "upToDate" }, update: null };
  } catch (error: unknown) {
    return { state: { status: "error", message: describeBridgeError(error) }, update: null };
  }
}

export function UpdateProvider({
  canInstall,
  children,
}: {
  canInstall: boolean;
  children: ReactNode;
}) {
  const [state, dispatch] = useReducer(updateReducer, { status: "checking" });
  const update = useRef<AvailableUpdate | null>(null);
  const { publish } = useNotificationCenter();

  const onChecked = useCallback(
    (check: StartupCheck) => {
      update.current = check.update;
      dispatch({ type: "checked", state: check.state });
      if (check.state.status === "available") {
        publish({ type: "updateAvailable", version: check.state.version });
      }
    },
    [publish],
  );

  const install = useCallback(() => {
    const available = update.current;
    if (available === null) {
      return;
    }
    if (!canInstall) {
      publish({ type: "updateDeferred" });
      return;
    }
    dispatch({ type: "downloadStarted" });
    available
      .install((downloaded, total) => {
        dispatch({ type: "progressed", downloaded, total });
      })
      .then(() => {
        dispatch({ type: "downloaded" });
      })
      .catch((error: unknown) => {
        dispatch({ type: "failed", message: describeBridgeError(error) });
      });
  }, [canInstall, publish]);
  useCommand(COMMANDS.installUpdate, install);

  return (
    <UpdateContext value={{ state, install }}>
      <Suspense fallback={null}>
        <StartupCheckResult onChecked={onChecked} />
      </Suspense>
      {children}
    </UpdateContext>
  );
}

function StartupCheckResult({ onChecked }: { onChecked: (check: StartupCheck) => void }) {
  const check = use(startupCheckPromise);
  useEffect(() => {
    onChecked(check);
  }, [check, onChecked]);
  return null;
}

export function useUpdateCenter(): UpdateCenter {
  const center = use(UpdateContext);
  if (center === null) {
    throw new Error("useUpdateCenter doit être utilisé dans un UpdateProvider.");
  }
  return center;
}

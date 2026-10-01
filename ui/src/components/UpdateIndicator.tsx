import { Suspense, use, useReducer } from "react";
import { describeBridgeError } from "../lib/tauri/engine";
import { findUpdate, isUpdaterConfigured, type AvailableUpdate } from "../lib/tauri/updater";
import { describeUpdate, updateReducer, type UpdateState } from "../lib/update-state";

interface InitialCheck {
  state: UpdateState;
  update: AvailableUpdate | null;
}

const BUSY_HINT = "Disponible une fois les traitements en cours terminés.";

const initialCheckPromise: Promise<InitialCheck> = checkAtStartup();

async function checkAtStartup(): Promise<InitialCheck> {
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

export function UpdateIndicator({ canInstall }: { canInstall: boolean }) {
  return (
    <Suspense fallback={<span className="status-item muted">Recherche de mises à jour…</span>}>
      <UpdateStatus canInstall={canInstall} />
    </Suspense>
  );
}

function UpdateStatus({ canInstall }: { canInstall: boolean }) {
  const initial = use(initialCheckPromise);
  const [state, dispatch] = useReducer(updateReducer, initial.state);
  const label = describeUpdate(state);

  const install = () => {
    const { update } = initial;
    if (update === null) {
      return;
    }
    dispatch({ type: "downloadStarted" });
    update
      .install((downloaded, total) => {
        dispatch({ type: "progressed", downloaded, total });
      })
      .then(() => {
        dispatch({ type: "downloaded" });
      })
      .catch((error: unknown) => {
        dispatch({ type: "failed", message: describeBridgeError(error) });
      });
  };

  if (state.status === "available") {
    return (
      <button
        type="button"
        className="status-update"
        disabled={!canInstall}
        title={canInstall ? "Télécharger et installer" : BUSY_HINT}
        onClick={install}
      >
        {label} — Installer
      </button>
    );
  }
  const title = state.status === "error" ? state.message : undefined;
  const tone = state.status === "error" ? "status-item error" : "status-item muted";
  return (
    <span className={tone} title={title}>
      {label}
    </span>
  );
}

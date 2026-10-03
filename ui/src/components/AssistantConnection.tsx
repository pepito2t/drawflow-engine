import { Suspense, use, useEffect, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import {
  parseAssistantStatus,
  selectableModels,
  type AssistantStatus,
} from "../lib/assistant-status";
import { toReadableError } from "../lib/error-message";
import { getAssistantModels } from "../lib/tauri/assistant";
import { saveSettings } from "../lib/tauri/engine";
import { ErrorBoundary } from "./ErrorBoundary";
import { Spinner } from "./Spinner";

function loadStatus(): Promise<AssistantStatus> {
  return getAssistantModels().then(parseAssistantStatus);
}

export function AssistantConnection({ onOpenSettings }: { onOpenSettings: () => void }) {
  const { id, promise, retry } = useRetryablePromise(loadStatus);
  const { subscribe } = useNotificationCenter();
  useEffect(
    () =>
      subscribe((event) => {
        if (event.type === "settingsSaved") {
          retry();
        }
      }),
    [subscribe, retry],
  );

  return (
    <ErrorBoundary
      key={id}
      fallback={(error) => (
        <ConnectionFailure
          label={toReadableError(error).message}
          onRetry={retry}
          onOpenSettings={onOpenSettings}
        />
      )}
    >
      <Suspense
        fallback={
          <div className="assistant-connection">
            <Spinner label="Connexion au modèle" />
            <span className="muted">Connexion au modèle…</span>
          </div>
        }
      >
        <ConnectionStatus statusPromise={promise} onRetry={retry} onOpenSettings={onOpenSettings} />
      </Suspense>
    </ErrorBoundary>
  );
}

interface ConnectionStatusProps {
  statusPromise: Promise<AssistantStatus>;
  onRetry: () => void;
  onOpenSettings: () => void;
}

function ConnectionStatus({ statusPromise, onRetry, onOpenSettings }: ConnectionStatusProps) {
  const status = use(statusPromise);
  const { publish } = useNotificationCenter();
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const chooseModel = (model: string) => {
    setIsSaving(true);
    setSaveError(null);
    saveSettings({ assistant: { model_server_url: status.server_url, model } })
      .then(() => {
        publish({ type: "settingsSaved" });
      })
      .catch((error: unknown) => {
        setSaveError(toReadableError(error).message);
        setIsSaving(false);
      });
  };

  return (
    <div className="assistant-connection" title={saveError ?? status.server_url}>
      <span className={`status-dot ${status.installed ? "ready" : "failed"}`} aria-hidden="true" />
      <select
        className="assistant-model"
        aria-label="Modèle de l'assistant"
        value={status.model}
        disabled={isSaving}
        onChange={(event) => {
          chooseModel(event.target.value);
        }}
      >
        {selectableModels(status).map((model) => (
          <option key={model} value={model}>
            {model === status.model && !status.installed ? `${model} (non installé)` : model}
          </option>
        ))}
      </select>
      {isSaving && <Spinner label="Changement de modèle" />}
      {saveError && <span className="assistant-connection-label assistant-error">{saveError}</span>}
      {!status.installed && (
        <button type="button" className="link-button" onClick={onRetry}>
          Réessayer
        </button>
      )}
      <button type="button" className="link-button" onClick={onOpenSettings}>
        Réglages
      </button>
    </div>
  );
}

interface ConnectionFailureProps {
  label: string;
  onRetry: () => void;
  onOpenSettings: () => void;
}

function ConnectionFailure({ label, onRetry, onOpenSettings }: ConnectionFailureProps) {
  return (
    <div className="assistant-connection" title={label}>
      <span className="status-dot failed" aria-hidden="true" />
      <span className="assistant-connection-label">{label}</span>
      <button type="button" className="link-button" onClick={onRetry}>
        Réessayer
      </button>
      <button type="button" className="link-button" onClick={onOpenSettings}>
        Réglages
      </button>
    </div>
  );
}

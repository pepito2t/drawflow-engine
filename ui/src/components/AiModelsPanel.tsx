import { Suspense, use, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { useSetupRun } from "../hooks/use-setup-run";
import { toReadableError } from "../lib/error-message";
import {
  formatSize,
  OLLAMA_LIBRARY_URL,
  parseModelCatalog,
  visibleModels,
  type ModelCatalog,
} from "../lib/model-catalog";
import type { SetupRun } from "../lib/setup";
import { deleteModel, getModelCatalog, pullModel } from "../lib/tauri/assistant";
import { saveSettings } from "../lib/tauri/engine";
import { openDownloadPage } from "../lib/tauri/setup";
import { ModelRow, TaskLine } from "./AiModelRow";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader } from "./Spinner";

function loadCatalog(): Promise<ModelCatalog> {
  return getModelCatalog().then(parseModelCatalog);
}

export function AiModelsPanel() {
  const { id, promise, retry } = useRetryablePromise(loadCatalog);
  const { run, start } = useSetupRun("models", retry);
  const download = (model: string) => {
    start(model, (onMessage) => pullModel(model, onMessage));
  };
  return (
    <section className="settings-section">
      <div className="setup-header">
        <h3>Modèles d'IA</h3>
        <button type="button" onClick={retry}>
          Actualiser
        </button>
      </div>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <ErrorPanel
              title="Catalogue indisponible"
              message={message}
              hint={hint}
              onRetry={retry}
            />
          );
        }}
      >
        <Suspense fallback={<Loader label="Chargement des modèles…" />}>
          <ModelList catalogPromise={promise} run={run} onDownload={download} onChanged={retry} />
        </Suspense>
      </ErrorBoundary>
    </section>
  );
}

interface ModelListProps {
  catalogPromise: Promise<ModelCatalog>;
  run: SetupRun;
  onDownload: (model: string) => void;
  onChanged: () => void;
}

function ModelList({ catalogPromise, run, onDownload, onChanged }: ModelListProps) {
  const catalog = use(catalogPromise);
  const { publish } = useNotificationCenter();
  const [query, setQuery] = useState("");
  const [other, setOther] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const isBusy = run.status === "running";

  const fail = (error: unknown) => {
    setActionError(toReadableError(error).message);
  };
  const chooseModel = (model: string) => {
    setActionError(null);
    saveSettings({ assistant: { model_server_url: catalog.server_url, model } })
      .then(() => {
        publish({ type: "settingsSaved" });
        onChanged();
      })
      .catch(fail);
  };
  const remove = (model: string) => {
    setActionError(null);
    deleteModel(model).then(onChanged).catch(fail);
  };

  return (
    <>
      <p className="muted">
        {catalog.memory_gb === null
          ? "Mémoire du poste inconnue."
          : `Mémoire du poste : ${formatSize(catalog.memory_gb)}.`}{" "}
        Recommandé : <strong>{catalog.recommended}</strong>.
      </p>
      {!catalog.is_ollama && (
        <ErrorPanel
          title="Ollama ne répond pas"
          message="Les téléchargements passent par Ollama."
          hint="Installez ou démarrez Ollama depuis Paramètres → Installation. Avec LM Studio, téléchargez les modèles depuis LM Studio."
        />
      )}
      <input
        type="text"
        value={query}
        placeholder="Rechercher un modèle…"
        aria-label="Rechercher un modèle"
        onChange={(event) => {
          setQuery(event.target.value);
        }}
      />
      <ul className="setup-list">
        {visibleModels(catalog, query).map((model) => (
          <ModelRow
            key={model.name}
            model={model}
            catalog={catalog}
            run={run}
            disabled={isBusy}
            onDownload={onDownload}
            onUse={chooseModel}
            onRemove={remove}
          />
        ))}
      </ul>
      {actionError && <ErrorPanel title="Action impossible" message={actionError} />}
      <div className="other-model">
        <input
          type="text"
          value={other}
          placeholder="Autre modèle de la bibliothèque Ollama (ex. mistral-nemo)"
          aria-label="Autre modèle"
          onChange={(event) => {
            setOther(event.target.value);
          }}
        />
        <button
          type="button"
          disabled={isBusy || !catalog.is_ollama || other.trim() === ""}
          onClick={() => {
            onDownload(other.trim());
          }}
        >
          Télécharger
        </button>
        <button
          type="button"
          className="link-button"
          onClick={() => {
            openDownloadPage(OLLAMA_LIBRARY_URL).catch(fail);
          }}
        >
          Parcourir la bibliothèque
        </button>
      </div>
      {run.status !== "idle" && !catalog.models.some((model) => model.name === run.action) && (
        <TaskLine run={run} />
      )}
    </>
  );
}

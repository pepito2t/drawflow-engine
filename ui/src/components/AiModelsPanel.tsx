import { Suspense, use, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { useSetupRun } from "../hooks/use-setup-run";
import { toReadableError } from "../lib/error-message";
import {
  fitsInMemory,
  formatSize,
  OLLAMA_LIBRARY_URL,
  parseModelCatalog,
  visibleModels,
  type CatalogEntry,
  type ModelCatalog,
} from "../lib/model-catalog";
import type { SetupRun } from "../lib/setup";
import { deleteModel, getModelCatalog, pullModel } from "../lib/tauri/assistant";
import { saveSettings } from "../lib/tauri/engine";
import { openDownloadPage } from "../lib/tauri/setup";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader } from "./Spinner";

function loadCatalog(): Promise<ModelCatalog> {
  return getModelCatalog().then(parseModelCatalog);
}

export function AiModelsPanel() {
  const { id, promise, retry } = useRetryablePromise(loadCatalog);
  const { run, start } = useSetupRun(retry);
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

interface ModelRowProps {
  model: CatalogEntry;
  catalog: ModelCatalog;
  run: SetupRun;
  disabled: boolean;
  onDownload: (model: string) => void;
  onUse: (model: string) => void;
  onRemove: (model: string) => void;
}

function ModelRow({ model, catalog, run, disabled, onDownload, onUse, onRemove }: ModelRowProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const isUsed = model.name === catalog.configured;
  const tooBig = !fitsInMemory(catalog, model);
  return (
    <li className="setup-item">
      <span className={`setup-status ${model.installed ? "ok" : "optional"}`}>
        {model.installed ? "Installé" : formatSize(model.size_gb)}
      </span>
      <div className="setup-body">
        <strong>
          {model.label}
          {model.name === catalog.recommended && <span className="badge">Recommandé</span>}
          {isUsed && <span className="badge">Utilisé</span>}
        </strong>
        <span className="muted">
          {model.name}
          {model.description && ` — ${model.description}`}
        </span>
        {tooBig && (
          <span className="assistant-error">
            Demande {model.min_memory_gb} Go de mémoire : risque d'être très lent sur ce poste.
          </span>
        )}
        {run.status !== "idle" && run.action === model.name && <TaskLine run={run} />}
        {confirmDelete && (
          <div className="setup-confirm">
            <span>Supprimer {model.name} de ce poste ?</span>
            <button
              type="button"
              className="primary"
              onClick={() => {
                setConfirmDelete(false);
                onRemove(model.name);
              }}
            >
              Supprimer
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirmDelete(false);
              }}
            >
              Annuler
            </button>
          </div>
        )}
      </div>
      <div className="setup-actions">
        {!model.installed && (
          <button
            type="button"
            className="primary"
            disabled={disabled || !catalog.is_ollama}
            onClick={() => {
              onDownload(model.name);
            }}
          >
            Télécharger
          </button>
        )}
        {model.installed && !isUsed && (
          <button
            type="button"
            className="primary"
            disabled={disabled}
            onClick={() => {
              onUse(model.name);
            }}
          >
            Utiliser
          </button>
        )}
        {model.installed && catalog.is_ollama && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              setConfirmDelete(true);
            }}
          >
            Supprimer
          </button>
        )}
      </div>
    </li>
  );
}

function TaskLine({ run }: { run: Exclude<SetupRun, { status: "idle" }> }) {
  switch (run.status) {
    case "running":
      return (
        <div className="setup-run">
          <progress value={run.percent ?? undefined} max={100} />
          <span className="muted">
            {run.action} : {run.message || "en cours…"}
            {run.percent !== null && ` · ${String(run.percent)} %`}
          </span>
        </div>
      );
    case "done":
      return <span className="run-status succeeded">{run.message || "Terminé"}</span>;
    case "failed":
      return (
        <ErrorPanel
          title="Téléchargement impossible"
          message={run.error.message}
          hint={run.error.hint}
        />
      );
  }
}

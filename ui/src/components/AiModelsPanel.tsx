import { Suspense, use, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { useSetupRun } from "../hooks/use-setup-run";
import { toReadableError } from "../lib/error-message";
import { t } from "../i18n/settings";
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
        <h3>{t("models.title")}</h3>
        <button type="button" onClick={retry}>
          {t("models.refresh")}
        </button>
      </div>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <ErrorPanel
              title={t("models.catalogError")}
              message={message}
              hint={hint}
              onRetry={retry}
            />
          );
        }}
      >
        <Suspense fallback={<Loader label={t("models.loading")} />}>
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
          ? t("models.memoryUnknown")
          : t("models.memory", { size: formatSize(catalog.memory_gb) })}{" "}
        {t("models.recommendedPrefix")} <strong>{catalog.recommended}</strong>.
      </p>
      {!catalog.is_ollama && (
        <ErrorPanel
          title={t("models.ollamaDown")}
          message={t("models.ollamaDownMessage")}
          hint={t("models.ollamaDownHint")}
        />
      )}
      <input
        type="text"
        value={query}
        placeholder={t("models.searchPlaceholder")}
        aria-label={t("models.search")}
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
      {actionError && <ErrorPanel title={t("models.actionError")} message={actionError} />}
      <div className="other-model">
        <input
          type="text"
          value={other}
          placeholder={t("models.otherPlaceholder")}
          aria-label={t("models.other")}
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
          {t("models.download")}
        </button>
        <button
          type="button"
          className="link-button"
          onClick={() => {
            openDownloadPage(OLLAMA_LIBRARY_URL).catch(fail);
          }}
        >
          {t("models.browseLibrary")}
        </button>
      </div>
      {run.status !== "idle" && !catalog.models.some((model) => model.name === run.action) && (
        <TaskLine run={run} />
      )}
    </>
  );
}

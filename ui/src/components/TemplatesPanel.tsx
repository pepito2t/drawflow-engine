import { Suspense, use, useCallback, useState } from "react";
import { useFileDrop, dropFieldProps } from "../hooks/use-file-drop";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { toReadableError, type ReadableError } from "../lib/error-message";
import {
  fileName,
  parseTemplateLibrary,
  TEMPLATE_FILTERS,
  templatesOfKind,
  type TemplateLibrary,
} from "../lib/templates";
import { pickPaths } from "../lib/tauri/dialog";
import { engineRequest, type EngineRequestName } from "../lib/tauri/engine";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { CloseIcon } from "./icons";
import { Loader, Spinner } from "./Spinner";

const DROP_NAMESPACE = "templates";
const DROP_FIELD = "library";
const NO_DEFAULT = "";

function loadLibrary(): Promise<TemplateLibrary> {
  return engineRequest("templates.list").then(parseTemplateLibrary);
}

export function TemplatesPanel() {
  const { id, promise, retry } = useRetryablePromise(loadLibrary);
  return (
    <ErrorBoundary
      key={id}
      fallback={(error) => {
        const { message, hint } = toReadableError(error);
        return (
          <ErrorPanel title="Modèles indisponibles" message={message} hint={hint} onRetry={retry} />
        );
      }}
    >
      <Suspense fallback={<Loader label="Chargement des modèles…" />}>
        <TemplatesEditor libraryPromise={promise} />
      </Suspense>
    </ErrorBoundary>
  );
}

function TemplatesEditor({ libraryPromise }: { libraryPromise: Promise<TemplateLibrary> }) {
  const [library, setLibrary] = useState(use(libraryPromise));
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<ReadableError | null>(null);
  const { publish } = useNotificationCenter();

  const request = useCallback(async (name: EngineRequestName, payload: Record<string, unknown>) => {
    setLibrary(parseTemplateLibrary(await engineRequest(name, payload)));
  }, []);

  const run = useCallback((task: () => Promise<void>) => {
    setIsBusy(true);
    setError(null);
    task()
      .catch((reason: unknown) => {
        setError(toReadableError(reason));
      })
      .finally(() => {
        setIsBusy(false);
      });
  }, []);

  const importFiles = useCallback(
    (paths: string[]) => {
      run(async () => {
        for (const path of paths) {
          await request("templates.import", { source: path });
          publish({ type: "templateImported", name: fileName(path) });
        }
      });
    },
    [publish, request, run],
  );

  const onDrop = useCallback(
    (_: string, paths: string[]) => {
      importFiles(paths);
    },
    [importFiles],
  );
  useFileDrop(DROP_NAMESPACE, onDrop);

  const browse = () => {
    pickPaths({
      directory: false,
      multiple: true,
      title: "Importer des modèles",
      filters: TEMPLATE_FILTERS,
    })
      .then(importFiles)
      .catch((reason: unknown) => {
        setError(toReadableError(reason));
      });
  };

  return (
    <section className="settings-section">
      <h3>Modèles</h3>
      <p className="muted">
        Importez vos modèles Excel (liste de pièces) et Word (rapport), puis choisissez le modèle
        utilisé par défaut. Un modèle choisi dans l'onglet reste prioritaire.
      </p>
      <div className="path-field" {...dropFieldProps(DROP_NAMESPACE, DROP_FIELD)}>
        <ul className="path-list">
          {library.templates.length === 0 && (
            <li className="placeholder">
              Glisser-déposer des fichiers .xlsx / .docx ici ou Importer…
            </li>
          )}
          {library.templates.map((template) => (
            <li key={template.id} className="template-row">
              <span className="template-kind">{template.kind.toUpperCase()}</span>
              <span title={template.id}>{template.id}</span>
              <button
                type="button"
                className="icon-button"
                aria-label={`Supprimer ${template.id}`}
                disabled={isBusy}
                onClick={() => {
                  run(() => request("templates.remove", { id: template.id }));
                }}
              >
                <CloseIcon size={14} />
              </button>
            </li>
          ))}
        </ul>
        <div className="path-actions">
          <button type="button" disabled={isBusy} onClick={browse}>
            Importer…
          </button>
        </div>
      </div>
      {library.modules.map((module) => (
        <div key={module.id} className="form-field">
          <label htmlFor={`default-${module.id}`}>Modèle par défaut — {module.name}</label>
          <select
            id={`default-${module.id}`}
            value={module.default ?? NO_DEFAULT}
            disabled={isBusy}
            onChange={(event) => {
              const template = event.target.value === NO_DEFAULT ? null : event.target.value;
              run(() => request("templates.set-default", { module: module.id, template }));
            }}
          >
            <option value={NO_DEFAULT}>Aucun (mise en page standard)</option>
            {templatesOfKind(library, module.kind).map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>
      ))}
      {isBusy && <Spinner label="Traitement" />}
      {error && (
        <ErrorPanel
          title="Opération impossible"
          message={error.message}
          hint={error.hint}
          file={error.file}
        />
      )}
    </section>
  );
}

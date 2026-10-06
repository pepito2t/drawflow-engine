import { Suspense, use, useState } from "react";
import { usePresets } from "../hooks/presets-context";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { describePresetTarget, newAutomation, validateAutomations } from "../lib/automations";
import type { CatalogModule } from "../lib/catalog";
import { toReadableError, type ReadableError } from "../lib/error-message";
import {
  getAutomationStatus,
  saveAutomations,
  type Automation,
  type AutomationStatus,
} from "../lib/tauri/automations";
import { pickPaths } from "../lib/tauri/dialog";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader, Spinner } from "./Spinner";

export function AutomationsPanel({ modules }: { modules: CatalogModule[] }) {
  const { id, promise, retry } = useRetryablePromise(getAutomationStatus);
  return (
    <ErrorBoundary
      key={id}
      fallback={(error) => {
        const { message, hint } = toReadableError(error);
        return (
          <ErrorPanel
            title="Automatisations indisponibles"
            message={message}
            hint={hint}
            onRetry={retry}
          />
        );
      }}
    >
      <Suspense fallback={<Loader label="Chargement…" />}>
        <AutomationsEditor statusPromise={promise} modules={modules} />
      </Suspense>
    </ErrorBoundary>
  );
}

interface AutomationsEditorProps {
  statusPromise: Promise<AutomationStatus>;
  modules: CatalogModule[];
}

function AutomationsEditor({ statusPromise, modules }: AutomationsEditorProps) {
  const initial = use(statusPromise);
  const { presets } = usePresets();
  const [automations, setAutomations] = useState(initial.automations);
  const [watchErrors, setWatchErrors] = useState(initial.errors);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<ReadableError | null>(null);
  const validation = validateAutomations(automations, presets);

  const update = (id: string, patch: Partial<Automation>) => {
    setSaved(false);
    setAutomations((current) =>
      current.map((automation) =>
        automation.id === id ? { ...automation, ...patch } : automation,
      ),
    );
  };

  const browse = (id: string) => {
    pickPaths({ directory: true, multiple: false, title: "Dossier à surveiller" })
      .then(([folder]) => {
        if (folder) {
          update(id, { folder });
        }
      })
      .catch((reason: unknown) => {
        setError(toReadableError(reason));
      });
  };

  const save = () => {
    setIsSaving(true);
    setError(null);
    saveAutomations(automations)
      .then((status) => {
        setAutomations(status.automations);
        setWatchErrors(status.errors);
        setSaved(true);
      })
      .catch((reason: unknown) => {
        setError(toReadableError(reason));
      })
      .finally(() => {
        setIsSaving(false);
      });
  };

  return (
    <section className="settings-section">
      <h3>Automatisations</h3>
      <p className="muted">
        Dès qu'un plan, un PDF ou un fichier Excel arrive dans un dossier surveillé, le préréglage
        choisi se lance avec ce fichier. Chaque fichier n'est traité qu'une fois ; l'application
        doit être ouverte et déverrouillée.
      </p>
      {presets.length === 0 && (
        <p className="muted">
          Créez d'abord un préréglage depuis le formulaire d'une fonctionnalité.
        </p>
      )}
      <ul className="automation-list">
        {automations.map((automation) => (
          <li key={automation.id} className="automation-item">
            <label className="automation-enabled">
              <input
                type="checkbox"
                checked={automation.enabled}
                disabled={isSaving}
                onChange={(event) => {
                  update(automation.id, { enabled: event.target.checked });
                }}
              />
              Active
            </label>
            <div className="automation-folder">
              <span className="path" title={automation.folder}>
                {automation.folder || "Aucun dossier choisi"}
              </span>
              <button
                type="button"
                disabled={isSaving}
                onClick={() => {
                  browse(automation.id);
                }}
              >
                Parcourir
              </button>
            </div>
            <select
              aria-label="Préréglage à lancer"
              value={automation.presetId}
              disabled={isSaving}
              onChange={(event) => {
                update(automation.id, { presetId: event.target.value });
              }}
            >
              <option value="">Préréglage…</option>
              {presets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {describePresetTarget(preset, modules)}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="icon-button"
              aria-label="Retirer cette automatisation"
              disabled={isSaving}
              onClick={() => {
                setSaved(false);
                setAutomations((current) => current.filter((item) => item.id !== automation.id));
              }}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      {watchErrors.map((message) => (
        <ErrorPanel key={message} title="Dossier non surveillé" message={message} />
      ))}
      {error && <ErrorPanel title="Automatisations non enregistrées" message={error.message} />}
      <div className="run-controls">
        <button
          type="button"
          disabled={isSaving || presets.length === 0}
          onClick={() => {
            setSaved(false);
            setAutomations((current) => [...current, newAutomation()]);
          }}
        >
          Ajouter un dossier
        </button>
        {validation && automations.length > 0 && <span className="muted">{validation}</span>}
        {saved && <span className="run-status succeeded">Automatisations enregistrées</span>}
        {isSaving && <Spinner label="Enregistrement" />}
        <button
          type="button"
          className="primary"
          disabled={isSaving || validation !== null}
          onClick={save}
        >
          Enregistrer
        </button>
      </div>
    </section>
  );
}

import { Suspense, use, useState } from "react";
import { usePresets } from "../hooks/presets-context";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { describePresetTarget, newAutomation, validateAutomations } from "../lib/automations";
import type { CatalogModule } from "../lib/catalog";
import { toReadableError, type ReadableError } from "../lib/error-message";
import { t } from "../i18n/settings";
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
            title={t("automations.unavailable")}
            message={message}
            hint={hint}
            onRetry={retry}
          />
        );
      }}
    >
      <Suspense fallback={<Loader label={t("automations.loading")} />}>
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
    pickPaths({ directory: true, multiple: false, title: t("automations.folderTitle") })
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
      <h3>{t("automations.title")}</h3>
      <p className="muted">{t("automations.intro")}</p>
      {presets.length === 0 && <p className="muted">{t("automations.noPresets")}</p>}
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
              {t("automations.enabled")}
            </label>
            <div className="automation-folder">
              <span className="path" title={automation.folder}>
                {automation.folder || t("automations.noFolder")}
              </span>
              <button
                type="button"
                disabled={isSaving}
                onClick={() => {
                  browse(automation.id);
                }}
              >
                {t("automations.browse")}
              </button>
            </div>
            <select
              aria-label={t("automations.presetLabel")}
              value={automation.presetId}
              disabled={isSaving}
              onChange={(event) => {
                update(automation.id, { presetId: event.target.value });
              }}
            >
              <option value="">{t("automations.presetPlaceholder")}</option>
              {presets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {describePresetTarget(preset, modules)}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="icon-button"
              aria-label={t("automations.remove")}
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
        <ErrorPanel key={message} title={t("automations.watchError")} message={message} />
      ))}
      {error && <ErrorPanel title={t("automations.notSaved")} message={error.message} />}
      <div className="run-controls">
        <button
          type="button"
          disabled={isSaving || presets.length === 0}
          onClick={() => {
            setSaved(false);
            setAutomations((current) => [...current, newAutomation()]);
          }}
        >
          {t("automations.addFolder")}
        </button>
        {validation && automations.length > 0 && <span className="muted">{validation}</span>}
        {saved && <span className="run-status succeeded">{t("automations.saved")}</span>}
        {isSaving && <Spinner label={t("automations.saving")} />}
        <button
          type="button"
          className="primary"
          disabled={isSaving || validation !== null}
          onClick={save}
        >
          {t("automations.save")}
        </button>
      </div>
    </section>
  );
}

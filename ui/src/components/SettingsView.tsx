import { Suspense, use, useCallback, useState, type SetStateAction } from "react";
import { useFieldDrop } from "../hooks/use-field-drop";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { toReadableError, type ReadableError } from "../lib/error-message";
import type { FormValue, FormValues } from "../lib/form-schema";
import {
  parseSettings,
  toSettingsPayload,
  valuesBySection,
  type SettingsSection,
  type SettingsValues,
} from "../lib/settings";
import { getSettings, saveSettings } from "../lib/tauri/engine";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { ModuleForm } from "./ModuleForm";
import { Loader, Spinner } from "./Spinner";

type SaveState =
  { status: "idle" | "saving" | "saved" } | { status: "failed"; error: ReadableError };

function loadSettings(): Promise<SettingsSection[]> {
  return getSettings().then(parseSettings);
}

export function SettingsView() {
  const { id, promise, retry } = useRetryablePromise(loadSettings);
  return (
    <ErrorBoundary
      key={id}
      fallback={(error) => {
        const { message, hint } = toReadableError(error);
        return (
          <ErrorPanel
            title="Impossible de charger les paramètres"
            message={message}
            hint={hint}
            onRetry={retry}
          />
        );
      }}
    >
      <Suspense fallback={<Loader label="Chargement des paramètres…" />}>
        <SettingsEditor sectionsPromise={promise} />
      </Suspense>
    </ErrorBoundary>
  );
}

function SettingsEditor({ sectionsPromise }: { sectionsPromise: Promise<SettingsSection[]> }) {
  const [sections, setSections] = useState(use(sectionsPromise));
  const [values, setValues] = useState<SettingsValues>(() => valuesBySection(sections));
  const [saveState, setSaveState] = useState<SaveState>({ status: "idle" });
  const isSaving = saveState.status === "saving";

  const save = () => {
    setSaveState({ status: "saving" });
    saveSettings(toSettingsPayload(sections, values))
      .then(parseSettings)
      .then((saved) => {
        setSections(saved);
        setValues(valuesBySection(saved));
        setSaveState({ status: "saved" });
      })
      .catch((error: unknown) => {
        setSaveState({ status: "failed", error: toReadableError(error) });
      });
  };

  return (
    <section className="module-workspace">
      <header>
        <h1>Paramètres</h1>
        <p>Normes et réglages appliqués à toutes les fonctionnalités.</p>
      </header>
      {sections.map((section) => (
        <SettingsSectionForm
          key={section.id}
          section={section}
          values={values[section.id] ?? section.values}
          disabled={isSaving}
          setValues={setValues}
        />
      ))}
      <div className="run-controls">
        <button type="button" className="primary" onClick={save} disabled={isSaving}>
          Enregistrer
        </button>
        {isSaving && <Spinner label="Enregistrement" />}
        {saveState.status === "saved" && (
          <span className="run-status succeeded">Paramètres enregistrés</span>
        )}
      </div>
      {saveState.status === "failed" && (
        <ErrorPanel
          title="Paramètres non enregistrés"
          message={saveState.error.message}
          hint={saveState.error.hint}
          file={saveState.error.file}
        />
      )}
    </section>
  );
}

interface SettingsSectionFormProps {
  section: SettingsSection;
  values: FormValues;
  disabled: boolean;
  setValues: (update: SetStateAction<SettingsValues>) => void;
}

function SettingsSectionForm({ section, values, disabled, setValues }: SettingsSectionFormProps) {
  const namespace = `settings-${section.id}`;
  const setSectionValues = useCallback(
    (update: SetStateAction<FormValues>) => {
      setValues((all) => {
        const current = all[section.id] ?? section.values;
        return { ...all, [section.id]: typeof update === "function" ? update(current) : update };
      });
    },
    [section.id, section.values, setValues],
  );
  useFieldDrop(namespace, section.fields, setSectionValues, disabled);

  return (
    <fieldset className="settings-section">
      <legend>{section.title}</legend>
      {section.error && (
        <ErrorPanel title="Valeurs enregistrées invalides" message={section.error} />
      )}
      <ModuleForm
        moduleId={namespace}
        fields={section.fields}
        values={values}
        disabled={disabled}
        onChange={(name: string, value: FormValue) => {
          setSectionValues((current) => ({ ...current, [name]: value }));
        }}
      />
    </fieldset>
  );
}

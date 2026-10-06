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
import type { CatalogModule } from "../lib/catalog";
import { AutomationsPanel } from "./AutomationsPanel";
import { ErrorBoundary } from "./ErrorBoundary";
import { useNotificationCenter } from "../hooks/notification-center";
import { t } from "../i18n/settings";
import { ErrorPanel } from "./ErrorPanel";
import { AboutPanel } from "./AboutPanel";
import { AccessCodeForm } from "./AccessCodeForm";
import { IntegrationsPanel } from "./IntegrationsPanel";
import { ProfilePanel } from "./ProfilePanel";
import { SectionTransfer } from "./SectionTransfer";
import { AI_MODELS_TAB_ID, SETUP_TAB_ID } from "../lib/setup";
import { AiModelsPanel } from "./AiModelsPanel";
import { SetupPanel } from "./SetupPanel";
import { TemplatesPanel } from "./TemplatesPanel";
import { CloseIcon } from "./icons";
import { ModuleForm } from "./ModuleForm";
import { Loader, Spinner } from "./Spinner";

const ACCESS_CODE_TAB_ID = "access-code";
const GENERAL_SECTION_ID = "general";
const TEMPLATES_TAB_ID = "templates";
const INTEGRATIONS_TAB_ID = "integrations";
const PROFILE_TAB_ID = "profile";
const ABOUT_TAB_ID = "about";
const AUTOMATIONS_TAB_ID = "automations";
const STATIC_TABS = [
  { id: SETUP_TAB_ID, title: "settings.tab.setup" },
  { id: AI_MODELS_TAB_ID, title: "settings.tab.aiModels" },
  { id: TEMPLATES_TAB_ID, title: "settings.tab.templates" },
  { id: AUTOMATIONS_TAB_ID, title: "settings.tab.automations" },
  { id: ACCESS_CODE_TAB_ID, title: "settings.tab.accessCode" },
  { id: INTEGRATIONS_TAB_ID, title: "settings.tab.integrations" },
  { id: PROFILE_TAB_ID, title: "settings.tab.profile" },
  { id: ABOUT_TAB_ID, title: "settings.tab.about" },
] as const;

type SaveState =
  { status: "idle" | "saving" | "saved" } | { status: "failed"; error: ReadableError };

function loadSettings(): Promise<SettingsSection[]> {
  return getSettings().then(parseSettings);
}

interface SettingsDialogProps {
  initialTab?: string | undefined;
  onClose: () => void;
  modules: CatalogModule[];
}

export function SettingsDialog({ initialTab, modules, onClose }: SettingsDialogProps) {
  const { id, promise, retry } = useRetryablePromise(loadSettings);
  return (
    <div
      className="dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          onClose();
        }
      }}
    >
      <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <header className="dialog-header">
          <h2 id="settings-title">{t("settings.title")}</h2>
          <button
            type="button"
            className="icon-button"
            aria-label={t("settings.close")}
            autoFocus
            onClick={onClose}
          >
            <CloseIcon />
          </button>
        </header>
        <SettingsContent
          attemptId={id}
          promise={promise}
          retry={retry}
          initialTab={initialTab}
          modules={modules}
        />
      </div>
    </div>
  );
}

interface SettingsContentProps {
  attemptId: number;
  promise: Promise<SettingsSection[]>;
  retry: () => void;
  initialTab: string | undefined;
  modules: CatalogModule[];
}

function SettingsContent({ attemptId, promise, retry, initialTab, modules }: SettingsContentProps) {
  return (
    <ErrorBoundary
      key={attemptId}
      fallback={(error) => {
        const { message, hint } = toReadableError(error);
        return (
          <div className="dialog-body centered">
            <ErrorPanel
              title={t("settings.loadError")}
              message={message}
              hint={hint}
              onRetry={retry}
            />
          </div>
        );
      }}
    >
      <Suspense
        fallback={
          <div className="dialog-body">
            <Loader label={t("settings.loading")} />
          </div>
        }
      >
        <SettingsEditor
          sectionsPromise={promise}
          initialTab={initialTab}
          modules={modules}
          onReload={retry}
        />
      </Suspense>
    </ErrorBoundary>
  );
}

interface SettingsEditorProps {
  sectionsPromise: Promise<SettingsSection[]>;
  modules: CatalogModule[];
  onReload: () => void;
  initialTab: string | undefined;
}

function SettingsEditor({ sectionsPromise, initialTab, modules, onReload }: SettingsEditorProps) {
  const [sections, setSections] = useState(use(sectionsPromise));
  const [values, setValues] = useState<SettingsValues>(() => valuesBySection(sections));
  const [saveState, setSaveState] = useState<SaveState>({ status: "idle" });
  const { publish } = useNotificationCenter();
  const [activeId, setActiveId] = useState(initialTab ?? sections[0]?.id ?? null);
  const isSaving = saveState.status === "saving";

  const save = () => {
    setSaveState({ status: "saving" });
    saveSettings(toSettingsPayload(sections, values))
      .then(parseSettings)
      .then((saved) => {
        setSections(saved);
        setValues(valuesBySection(saved));
        setSaveState({ status: "saved" });
        publish({ type: "settingsSaved" });
      })
      .catch((error: unknown) => {
        setSaveState({ status: "failed", error: toReadableError(error) });
      });
  };

  const isStaticTab = STATIC_TABS.some((tab) => tab.id === activeId);
  const activeSection = isStaticTab
    ? undefined
    : (sections.find((section) => section.id === activeId) ?? sections[0]);

  return (
    <>
      <div className="dialog-body settings-layout">
        <nav
          className="side-tabs"
          role="tablist"
          aria-orientation="vertical"
          aria-label={t("settings.categories")}
        >
          {sections.map((section) => (
            <button
              key={section.id}
              type="button"
              role="tab"
              aria-selected={section.id === activeSection?.id}
              className={section.id === activeSection?.id ? "side-tab selected" : "side-tab"}
              onClick={() => {
                setActiveId(section.id);
              }}
            >
              <span>{section.title}</span>
              {section.error && <span className="status-dot failed" />}
            </button>
          ))}
          {STATIC_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeId === tab.id}
              className={activeId === tab.id ? "side-tab selected" : "side-tab"}
              onClick={() => {
                setActiveId(tab.id);
              }}
            >
              <span>{t(tab.title)}</span>
            </button>
          ))}
        </nav>
        <div className="settings-panel">
          {activeId === SETUP_TAB_ID && <SetupPanel onOpenTab={setActiveId} />}
          {activeId === AI_MODELS_TAB_ID && <AiModelsPanel />}
          {activeId === TEMPLATES_TAB_ID && <TemplatesPanel />}
          {activeId === INTEGRATIONS_TAB_ID && <IntegrationsPanel />}
          {activeId === PROFILE_TAB_ID && <ProfilePanel onImported={onReload} />}
          {activeId === ABOUT_TAB_ID && (
            <AboutPanel
              onOpenGeneral={() => {
                setActiveId(GENERAL_SECTION_ID);
              }}
            />
          )}
          {activeId === AUTOMATIONS_TAB_ID && <AutomationsPanel modules={modules} />}
          {activeId === ACCESS_CODE_TAB_ID && <AccessCodeForm />}
          {sections.map((section) => (
            <div key={section.id} role="tabpanel" hidden={section.id !== activeSection?.id}>
              <SettingsSectionForm
                section={section}
                values={values[section.id] ?? section.values}
                disabled={isSaving}
                setValues={setValues}
              />
            </div>
          ))}
        </div>
      </div>
      <footer className="dialog-footer" hidden={isStaticTab}>
        {saveState.status === "failed" && (
          <ErrorPanel
            title={t("settings.notSaved")}
            message={saveState.error.message}
            hint={saveState.error.hint}
            file={saveState.error.file}
          />
        )}
        <div className="run-controls">
          {saveState.status === "saved" && (
            <span className="run-status succeeded">{t("settings.saved")}</span>
          )}
          {isSaving && <Spinner label={t("settings.saving")} />}
          <button type="button" className="primary" onClick={save} disabled={isSaving}>
            {t("settings.save")}
          </button>
        </div>
      </footer>
    </>
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
    <section className="settings-section">
      <h3>{section.title}</h3>
      {section.id !== GENERAL_SECTION_ID && (
        <SectionTransfer
          section={section}
          disabled={disabled}
          onImported={(imported) => {
            setSectionValues(imported);
          }}
        />
      )}
      {section.error && <ErrorPanel title={t("settings.invalidValues")} message={section.error} />}
      <ModuleForm
        moduleId={namespace}
        fields={section.fields}
        values={values}
        disabled={disabled}
        onChange={(name: string, value: FormValue) => {
          setSectionValues((current) => ({ ...current, [name]: value }));
        }}
      />
    </section>
  );
}

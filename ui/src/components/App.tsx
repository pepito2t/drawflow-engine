import { t } from "../i18n/shell";
import { Suspense, use, useCallback, useState } from "react";
import { RunsProvider, useRunsSelector, useRunsState, useRunsStore } from "../hooks/runs-context";
import { SetupRunsProvider } from "../hooks/setup-runs-context";
import { runningModuleIds } from "../lib/runs-store";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { CommandProvider } from "../hooks/command-registry";
import { NotificationProvider } from "../hooks/notification-center";
import { HistoryProvider } from "../hooks/history-context";
import { SettingsFeedProvider } from "../hooks/settings-feed";
import { loadPresets, PresetsProvider } from "../hooks/presets-context";
import { UpdateProvider } from "../hooks/update-center";
import { useAppCommands } from "../hooks/use-app-commands";
import { useGlobalShortcuts } from "../hooks/use-global-shortcuts";
import { useIntegrationBridge } from "../hooks/use-integration-bridge";
import { useLanguage } from "../hooks/use-language";
import { loadCatalog, useModuleCatalog } from "../hooks/use-module-catalog";
import { useRunEvents } from "../hooks/use-run-events";
import { useSetupCheck } from "../hooks/use-setup-check";
import { useSystemNotifications } from "../hooks/use-system-notifications";
import { useLanguageSync } from "../hooks/use-language-sync";
import type { CatalogModule } from "../lib/catalog";
import { toReadableError } from "../lib/error-message";
import type { Preset } from "../lib/presets";
import { getLockStatus, type LockStatus } from "../lib/tauri/access";
import { AppShell } from "./AppShell";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { AssistantPanel } from "./AssistantPanel";
import { HelpDialog } from "./HelpDialog";
import { ChatIcon, GearIcon, HelpIcon, ClockIcon, MailIcon, SunIcon } from "./icons";
import { LockScreen } from "./LockScreen";
import { ModuleTabs, tabPanelId } from "./ModuleTabs";
import { SettingsDialog } from "./SettingsDialog";
import { HistoryPanel } from "./HistoryPanel";
import { MailPanel } from "./MailPanel";
import { TodayPanel } from "./TodayPanel";
import { ModuleWorkspace } from "./ModuleWorkspace";
import { RunsIndicator } from "./RunsIndicator";
import { Toaster } from "./Toaster";
import { UpdateIndicator } from "./UpdateIndicator";
import { Loader } from "./Spinner";

export const HISTORY_TAB_ID = "history";
export const TODAY_TAB_ID = "today";
export const MAIL_TAB_ID = "mail";
const SPECIAL_TABS = new Set([HISTORY_TAB_ID, TODAY_TAB_ID, MAIL_TAB_ID]);
const MAIL_SETTINGS_TAB = "mail";
const DEFAULT_SETTINGS_TAB = "";
const ASSISTANT_SETTINGS_TAB = "assistant";

interface Startup {
  modules: CatalogModule[];
  presets: Preset[];
}

/** Both come from the engine at start; one Retry recovers either of them. */
async function loadStartup(): Promise<Startup> {
  const [modules, presets] = await Promise.all([loadCatalog(), loadPresets()]);
  return { modules, presets };
}

export function App() {
  useLanguage();
  const { id, promise, retry } = useRetryablePromise(getLockStatus);
  return (
    <ErrorBoundary key={id} fallback={(error) => <CatalogFailure error={error} onRetry={retry} />}>
      <Suspense
        fallback={
          <AppShell engine={{ state: "loading" }}>
            <Loader label={t("app.starting")} />
          </AppShell>
        }
      >
        <LockGate statusPromise={promise} />
      </Suspense>
    </ErrorBoundary>
  );
}

function LockGate({ statusPromise }: { statusPromise: Promise<LockStatus> }) {
  const status = use(statusPromise);
  const [isUnlocked, setIsUnlocked] = useState(status.unlocked);
  if (!isUnlocked) {
    return (
      <AppShell engine={{ state: "loading" }}>
        <LockScreen
          onUnlocked={() => {
            setIsUnlocked(true);
          }}
        />
      </AppShell>
    );
  }
  return <CatalogApp />;
}

function CatalogApp() {
  const { id, promise, retry } = useRetryablePromise(loadStartup);

  return (
    <ErrorBoundary key={id} fallback={(error) => <CatalogFailure error={error} onRetry={retry} />}>
      <Suspense
        fallback={
          <AppShell engine={{ state: "loading" }}>
            <Loader label={t("app.startingEngine")} />
          </AppShell>
        }
      >
        <RunsProvider>
          <SetupRunsProvider>
            <NotificationProvider>
              <SettingsFeedProvider>
                <CommandProvider>
                  <StartupGate startupPromise={promise} />
                </CommandProvider>
              </SettingsFeedProvider>
            </NotificationProvider>
          </SetupRunsProvider>
        </RunsProvider>
      </Suspense>
    </ErrorBoundary>
  );
}

function StartupGate({ startupPromise }: { startupPromise: Promise<Startup> }) {
  const { modules, presets } = use(startupPromise);
  return (
    <PresetsProvider initialPresets={presets}>
      <HistoryProvider>
        <CatalogView initialModules={modules} />
      </HistoryProvider>
    </PresetsProvider>
  );
}

function CatalogFailure({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { message, hint } = toReadableError(error);
  return (
    <AppShell engine={{ state: "failed" }}>
      <div className="centered">
        <ErrorPanel
          title={t("app.engineStartFailed")}
          message={message}
          hint={hint}
          onRetry={onRetry}
        />
      </div>
    </AppShell>
  );
}

function CatalogView({ initialModules }: { initialModules: CatalogModule[] }) {
  const modules = useModuleCatalog(initialModules);
  const [selectedId, setSelectedId] = useState<string | null>(TODAY_TAB_ID);
  const [settingsTab, setSettingsTab] = useState<string | null>(null);
  const [help, setHelp] = useState<{ topic: string | undefined } | null>(null);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const { dispatch } = useRunsStore();
  const canInstallUpdate = useRunsSelector((state) => runningModuleIds(state).length === 0);
  useLanguageSync();
  useSystemNotifications();
  useSetupCheck();

  const select = useCallback(
    (tabId: string) => {
      for (const visited of [selectedId, tabId]) {
        if (visited !== null && !SPECIAL_TABS.has(visited)) {
          dispatch({ type: "acknowledge", moduleId: visited });
        }
      }
      setSelectedId(tabId);
    },
    [dispatch, selectedId],
  );
  const openHistory = useCallback(() => {
    select(HISTORY_TAB_ID);
  }, [select]);
  const openToday = useCallback(() => {
    select(TODAY_TAB_ID);
  }, [select]);
  const openMail = useCallback(() => {
    select(MAIL_TAB_ID);
  }, [select]);
  const openSettings = useCallback((tab?: string) => {
    setSettingsTab(tab ?? DEFAULT_SETTINGS_TAB);
  }, []);
  const toggleAssistant = useCallback(() => {
    setIsAssistantOpen((open) => !open);
  }, []);
  const openHelp = useCallback((topic?: string) => {
    setHelp({ topic });
  }, []);
  useAppCommands({
    modules,
    selectedId,
    selectModule: select,
    openSettings,
    toggleAssistant,
    openHelp,
    openHistory,
    openToday,
    openMail,
  });
  useIntegrationBridge();
  useGlobalShortcuts();

  const sidebarActions = (
    <>
      <button
        type="button"
        className="icon-button"
        aria-label={t("app.settings")}
        aria-keyshortcuts="Control+,"
        title={t("app.settings")}
        onClick={() => {
          openSettings();
        }}
      >
        <GearIcon />
      </button>
      <RunsIndicator modules={modules} onOpenModule={select} />
      <button
        type="button"
        className={isAssistantOpen ? "icon-button active" : "icon-button"}
        aria-label={t("app.assistant")}
        aria-expanded={isAssistantOpen}
        title={t("app.assistant")}
        onClick={toggleAssistant}
      >
        <ChatIcon />
      </button>
      <button
        type="button"
        className="icon-button"
        aria-label={t("app.help")}
        aria-keyshortcuts="F1"
        title={t("app.help")}
        onClick={() => {
          openHelp();
        }}
      >
        <HelpIcon />
      </button>
    </>
  );

  return (
    <UpdateProvider canInstall={canInstallUpdate}>
      <AppShell
        engine={{ state: "ready", moduleCount: modules.length }}
        updates={<UpdateIndicator />}
      >
        <div className={isAssistantOpen ? "layout with-assistant" : "layout"}>
          <ModuleTabs
            modules={modules}
            leadingTabs={[{ id: TODAY_TAB_ID, label: t("app.todayTab"), icon: <SunIcon /> }]}
            extraTabs={[
              { id: MAIL_TAB_ID, label: t("app.mailTab"), icon: <MailIcon /> },
              { id: HISTORY_TAB_ID, label: t("app.historyTab"), icon: <ClockIcon /> },
            ]}
            selectedId={selectedId}
            onSelect={select}
            footer={sidebarActions}
          />
          <main className="workspace">
            {modules.length === 0 && <p className="muted">{t("app.noModules")}</p>}
            {modules.map((module) => (
              <div
                key={module.manifest.id}
                role="tabpanel"
                id={tabPanelId(module.manifest.id)}
                hidden={selectedId !== module.manifest.id}
              >
                <ModuleWorkspace module={module} />
              </div>
            ))}
            <div role="tabpanel" id={tabPanelId(TODAY_TAB_ID)} hidden={selectedId !== TODAY_TAB_ID}>
              <TodayPanel modules={modules} />
            </div>
            <div
              role="tabpanel"
              id={tabPanelId(HISTORY_TAB_ID)}
              hidden={selectedId !== HISTORY_TAB_ID}
            >
              <HistoryPanel />
            </div>
            <div role="tabpanel" id={tabPanelId(MAIL_TAB_ID)} hidden={selectedId !== MAIL_TAB_ID}>
              <MailPanel
                onOpenSettings={() => {
                  openSettings(MAIL_SETTINGS_TAB);
                }}
              />
            </div>
          </main>
          <AssistantPanel
            modules={modules}
            isOpen={isAssistantOpen}
            onClose={() => {
              setIsAssistantOpen(false);
            }}
            onOpenSettings={() => {
              openSettings(ASSISTANT_SETTINGS_TAB);
            }}
          />
        </div>
        <RunEventsPublisher modules={modules} />
        <Toaster onOpenModule={select} />
        {settingsTab !== null && (
          <SettingsDialog
            key={settingsTab}
            modules={modules}
            initialTab={settingsTab === DEFAULT_SETTINGS_TAB ? undefined : settingsTab}
            onClose={() => {
              setSettingsTab(null);
            }}
          />
        )}
        {help !== null && (
          <HelpDialog
            key={help.topic ?? ""}
            topic={help.topic}
            onClose={() => {
              setHelp(null);
            }}
          />
        )}
      </AppShell>
    </UpdateProvider>
  );
}

/** Follows every run message; isolated so the rest of the screen does not re-render with it. */
function RunEventsPublisher({ modules }: { modules: CatalogModule[] }) {
  useRunEvents(useRunsState(), modules);
  return null;
}

import { Suspense, use, useCallback, useState } from "react";
import { RunsProvider, useRunsStore } from "../hooks/runs-context";
import { SetupRunsProvider } from "../hooks/setup-runs-context";
import { runningModuleIds } from "../lib/runs-store";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { CommandProvider } from "../hooks/command-registry";
import { NotificationProvider } from "../hooks/notification-center";
import { loadPresets, PresetsProvider } from "../hooks/presets-context";
import { UpdateProvider } from "../hooks/update-center";
import { useAppCommands } from "../hooks/use-app-commands";
import { useIntegrationBridge } from "../hooks/use-integration-bridge";
import { useRunEvents } from "../hooks/use-run-events";
import { useSetupCheck } from "../hooks/use-setup-check";
import { useSystemNotifications } from "../hooks/use-system-notifications";
import { parseCatalog, type CatalogModule } from "../lib/catalog";
import { toReadableError } from "../lib/error-message";
import { getLockStatus, type LockStatus } from "../lib/tauri/access";
import { listModules } from "../lib/tauri/engine";
import { AppShell } from "./AppShell";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { AssistantPanel } from "./AssistantPanel";
import { HelpDialog } from "./HelpDialog";
import { ChatIcon, GearIcon, HelpIcon, ClockIcon, SunIcon } from "./icons";
import { LockScreen } from "./LockScreen";
import { ModuleTabs, tabPanelId } from "./ModuleTabs";
import { SettingsDialog } from "./SettingsDialog";
import { HistoryPanel } from "./HistoryPanel";
import { TodayPanel } from "./TodayPanel";
import { ModuleWorkspace } from "./ModuleWorkspace";
import { RunsIndicator } from "./RunsIndicator";
import { Toaster } from "./Toaster";
import { UpdateIndicator } from "./UpdateIndicator";
import { Loader } from "./Spinner";

export const HISTORY_TAB_ID = "history";
export const TODAY_TAB_ID = "today";
const SPECIAL_TABS = new Set([HISTORY_TAB_ID, TODAY_TAB_ID]);
const DEFAULT_SETTINGS_TAB = "";
const ASSISTANT_SETTINGS_TAB = "assistant";

function loadCatalog(): Promise<CatalogModule[]> {
  return listModules().then(parseCatalog);
}

export function App() {
  const { id, promise, retry } = useRetryablePromise(getLockStatus);
  return (
    <ErrorBoundary key={id} fallback={(error) => <CatalogFailure error={error} onRetry={retry} />}>
      <Suspense
        fallback={
          <AppShell engine={{ state: "loading" }}>
            <Loader label="Démarrage…" />
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
  const { id, promise, retry } = useRetryablePromise(loadCatalog);
  const [presetsPromise] = useState(loadPresets);

  return (
    <ErrorBoundary key={id} fallback={(error) => <CatalogFailure error={error} onRetry={retry} />}>
      <Suspense
        fallback={
          <AppShell engine={{ state: "loading" }}>
            <Loader label="Démarrage du moteur…" />
          </AppShell>
        }
      >
        <RunsProvider>
          <SetupRunsProvider>
            <NotificationProvider>
              <CommandProvider>
                <PresetsProvider presetsPromise={presetsPromise}>
                  <CatalogView catalogPromise={promise} />
                </PresetsProvider>
              </CommandProvider>
            </NotificationProvider>
          </SetupRunsProvider>
        </RunsProvider>
      </Suspense>
    </ErrorBoundary>
  );
}

function CatalogFailure({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { message, hint } = toReadableError(error);
  return (
    <AppShell engine={{ state: "failed" }}>
      <div className="centered">
        <ErrorPanel
          title="Impossible de démarrer le moteur"
          message={message}
          hint={hint}
          onRetry={onRetry}
        />
      </div>
    </AppShell>
  );
}

function CatalogView({ catalogPromise }: { catalogPromise: Promise<CatalogModule[]> }) {
  const modules = use(catalogPromise);
  const [selectedId, setSelectedId] = useState<string | null>(TODAY_TAB_ID);
  const [settingsTab, setSettingsTab] = useState<string | null>(null);
  const [help, setHelp] = useState<{ topic: string | undefined } | null>(null);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const { state, dispatch } = useRunsStore();
  useRunEvents(state, modules);
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
    selectModule: select,
    openSettings,
    toggleAssistant,
    openHelp,
    openHistory,
    openToday,
  });
  useIntegrationBridge();

  const sidebarActions = (
    <>
      <button
        type="button"
        className="icon-button"
        aria-label="Paramètres"
        title="Paramètres"
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
        aria-label="Assistant"
        aria-expanded={isAssistantOpen}
        title="Assistant"
        onClick={toggleAssistant}
      >
        <ChatIcon />
      </button>
      <button
        type="button"
        className="icon-button"
        aria-label="Aide"
        title="Aide"
        onClick={() => {
          openHelp();
        }}
      >
        <HelpIcon />
      </button>
    </>
  );

  return (
    <UpdateProvider canInstall={runningModuleIds(state).length === 0}>
      <AppShell
        engine={{ state: "ready", moduleCount: modules.length }}
        updates={<UpdateIndicator />}
      >
        <div className={isAssistantOpen ? "layout with-assistant" : "layout"}>
          <ModuleTabs
            modules={modules}
            leadingTabs={[{ id: TODAY_TAB_ID, label: "Aujourd'hui", icon: <SunIcon /> }]}
            extraTabs={[{ id: HISTORY_TAB_ID, label: "Historique", icon: <ClockIcon /> }]}
            selectedId={selectedId}
            onSelect={select}
            footer={sidebarActions}
          />
          <main className="workspace">
            {modules.length === 0 && <p className="muted">Aucune fonctionnalité disponible.</p>}
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
        <Toaster onOpenModule={select} />
        {settingsTab !== null && (
          <SettingsDialog
            key={settingsTab}
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

import { Suspense, use, useCallback, useState } from "react";
import { RunsProvider, useRunsStore } from "../hooks/runs-context";
import { runningModuleIds } from "../lib/runs-store";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { CommandProvider } from "../hooks/command-registry";
import { NotificationProvider } from "../hooks/notification-center";
import { loadPresets, PresetsProvider } from "../hooks/presets-context";
import { UpdateProvider } from "../hooks/update-center";
import { useAppCommands } from "../hooks/use-app-commands";
import { useRunEvents } from "../hooks/use-run-events";
import { useSystemNotifications } from "../hooks/use-system-notifications";
import { parseCatalog, type CatalogModule } from "../lib/catalog";
import { toReadableError } from "../lib/error-message";
import { getLockStatus, type LockStatus } from "../lib/tauri/access";
import { listModules } from "../lib/tauri/engine";
import { AppShell } from "./AppShell";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { GearIcon } from "./icons";
import { LockScreen } from "./LockScreen";
import { ModuleTabs, tabPanelId } from "./ModuleTabs";
import { SettingsDialog } from "./SettingsDialog";
import { ModuleWorkspace } from "./ModuleWorkspace";
import { RunsIndicator } from "./RunsIndicator";
import { Toaster } from "./Toaster";
import { UpdateIndicator } from "./UpdateIndicator";
import { Loader } from "./Spinner";

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
          <NotificationProvider>
            <CommandProvider>
              <PresetsProvider presetsPromise={presetsPromise}>
                <CatalogView catalogPromise={promise} />
              </PresetsProvider>
            </CommandProvider>
          </NotificationProvider>
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
  const [selectedId, setSelectedId] = useState(modules[0]?.manifest.id ?? null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { state, dispatch } = useRunsStore();
  useRunEvents(state, modules);
  useSystemNotifications();

  const select = useCallback(
    (moduleId: string) => {
      setSelectedId((previous) => {
        for (const visited of [previous, moduleId]) {
          if (visited !== null) {
            dispatch({ type: "acknowledge", moduleId: visited });
          }
        }
        return moduleId;
      });
    },
    [dispatch],
  );
  const openSettings = useCallback(() => {
    setIsSettingsOpen(true);
  }, []);
  useAppCommands({ modules, selectModule: select, openSettings });

  const sidebarActions = (
    <>
      <button
        type="button"
        className="icon-button"
        aria-label="Paramètres"
        title="Paramètres"
        onClick={() => {
          setIsSettingsOpen(true);
        }}
      >
        <GearIcon />
      </button>
      <RunsIndicator modules={modules} onOpenModule={select} />
    </>
  );

  return (
    <UpdateProvider canInstall={runningModuleIds(state).length === 0}>
      <AppShell
        engine={{ state: "ready", moduleCount: modules.length }}
        updates={<UpdateIndicator />}
      >
        <div className="layout">
          <ModuleTabs
            modules={modules}
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
          </main>
        </div>
        <Toaster onOpenModule={select} />
        {isSettingsOpen && (
          <SettingsDialog
            onClose={() => {
              setIsSettingsOpen(false);
            }}
          />
        )}
      </AppShell>
    </UpdateProvider>
  );
}

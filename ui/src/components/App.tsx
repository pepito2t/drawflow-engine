import { Suspense, use, useState } from "react";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { parseCatalog, type CatalogModule } from "../lib/catalog";
import { toReadableError } from "../lib/error-message";
import { listModules } from "../lib/tauri/engine";
import { AppShell } from "./AppShell";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { ModuleTabs, SETTINGS_PANEL_ID, tabPanelId, type Selection } from "./ModuleTabs";
import { SettingsView } from "./SettingsView";
import { ModuleWorkspace } from "./ModuleWorkspace";
import { Loader } from "./Spinner";

function loadCatalog(): Promise<CatalogModule[]> {
  return listModules().then(parseCatalog);
}

export function App() {
  const { id, promise, retry } = useRetryablePromise(loadCatalog);

  return (
    <ErrorBoundary key={id} fallback={(error) => <CatalogFailure error={error} onRetry={retry} />}>
      <Suspense
        fallback={
          <AppShell engine={{ state: "loading" }}>
            <Loader label="Démarrage du moteur…" />
          </AppShell>
        }
      >
        <CatalogView catalogPromise={promise} />
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
  const firstModuleId = modules[0]?.manifest.id;
  const [selection, setSelection] = useState<Selection | null>(
    firstModuleId ? { kind: "module", id: firstModuleId } : { kind: "settings" },
  );
  const isModuleSelected = (moduleId: string) =>
    selection?.kind === "module" && selection.id === moduleId;

  return (
    <AppShell engine={{ state: "ready", moduleCount: modules.length }}>
      <div className="layout">
        <ModuleTabs modules={modules} selection={selection} onSelect={setSelection} />
        <main className="workspace">
          {modules.length === 0 && <p className="muted">Aucune fonctionnalité disponible.</p>}
          {modules.map((module) => (
            <div
              key={module.manifest.id}
              role="tabpanel"
              id={tabPanelId(module.manifest.id)}
              hidden={!isModuleSelected(module.manifest.id)}
            >
              <ModuleWorkspace module={module} />
            </div>
          ))}
          {selection?.kind === "settings" && (
            <div role="tabpanel" id={SETTINGS_PANEL_ID}>
              <SettingsView />
            </div>
          )}
        </main>
      </div>
    </AppShell>
  );
}

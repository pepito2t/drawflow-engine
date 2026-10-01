import { Suspense, use, useCallback, useState } from "react";
import { parseCatalog, type CatalogModule } from "../lib/catalog";
import { toReadableError } from "../lib/error-message";
import { listModules } from "../lib/tauri/engine";
import { AppShell } from "./AppShell";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { ModuleTabs, tabPanelId } from "./ModuleTabs";
import { ModuleWorkspace } from "./ModuleWorkspace";
import { Loader } from "./Spinner";

interface CatalogAttempt {
  id: number;
  promise: Promise<CatalogModule[]>;
}

function loadCatalog(): Promise<CatalogModule[]> {
  return listModules().then(parseCatalog);
}

export function App() {
  const [attempt, setAttempt] = useState<CatalogAttempt>(() => ({ id: 0, promise: loadCatalog() }));
  const retry = useCallback(() => {
    setAttempt((current) => ({ id: current.id + 1, promise: loadCatalog() }));
  }, []);

  return (
    <ErrorBoundary
      key={attempt.id}
      fallback={(error) => <CatalogFailure error={error} onRetry={retry} />}
    >
      <Suspense
        fallback={
          <AppShell engine={{ state: "loading" }}>
            <Loader label="Démarrage du moteur…" />
          </AppShell>
        }
      >
        <CatalogView catalogPromise={attempt.promise} />
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

  return (
    <AppShell engine={{ state: "ready", moduleCount: modules.length }}>
      <div className="layout">
        <ModuleTabs modules={modules} selectedId={selectedId} onSelect={setSelectedId} />
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
    </AppShell>
  );
}

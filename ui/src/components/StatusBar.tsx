import { Suspense, use } from "react";
import { getAppVersion } from "../lib/tauri/app";
import { UpdateIndicator } from "./UpdateIndicator";

export type EngineStatus =
  { state: "loading" } | { state: "ready"; moduleCount: number } | { state: "failed" };

const UNKNOWN_VERSION = "?";

const appVersionPromise: Promise<string> = getAppVersion().catch((error: unknown) => {
  console.error("Version de l'application indisponible :", error);
  return UNKNOWN_VERSION;
});

interface StatusBarProps {
  engine: EngineStatus;
  canInstallUpdate: boolean;
}

export function StatusBar({ engine, canInstallUpdate }: StatusBarProps) {
  return (
    <footer className="status-bar">
      <div className="status-group">
        <EngineIndicator engine={engine} />
      </div>
      <div className="status-group">
        <UpdateIndicator canInstall={canInstallUpdate} />
        <span className="status-item">
          Drawflow v
          <Suspense fallback="…">
            <AppVersion />
          </Suspense>
        </span>
      </div>
    </footer>
  );
}

function AppVersion() {
  return use(appVersionPromise);
}

function EngineIndicator({ engine }: { engine: EngineStatus }) {
  return (
    <span className="status-item">
      <span className={`status-dot ${engine.state}`} aria-hidden="true" />
      {describeEngine(engine)}
    </span>
  );
}

function describeEngine(engine: EngineStatus): string {
  switch (engine.state) {
    case "loading":
      return "Démarrage du moteur…";
    case "failed":
      return "Moteur indisponible";
    case "ready":
      return `Moteur prêt · ${String(engine.moduleCount)} fonctionnalité${engine.moduleCount > 1 ? "s" : ""}`;
  }
}

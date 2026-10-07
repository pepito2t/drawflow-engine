import { plural } from "../i18n";
import { t as consoleText } from "../i18n/console";
import { t } from "../i18n/shell";
import { Suspense, use, type ReactNode } from "react";
import { useOptionalConsole } from "../hooks/console-context";
import { useLanguage } from "../hooks/use-language";
import { getAppVersion } from "../lib/tauri/app";

export type EngineStatus =
  { state: "loading" } | { state: "ready"; moduleCount: number } | { state: "failed" };

const UNKNOWN_VERSION = "?";

const appVersionPromise: Promise<string> = getAppVersion().catch((error: unknown) => {
  console.error("Version de l'application indisponible :", error);
  return UNKNOWN_VERSION;
});

interface StatusBarProps {
  engine: EngineStatus;
  updates?: ReactNode;
}

export function StatusBar({ engine, updates }: StatusBarProps) {
  useLanguage();
  return (
    <footer className="status-bar">
      <div className="status-group">
        <EngineIndicator engine={engine} />
      </div>
      <div className="status-group">
        <ConsoleButton />
        {updates}
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

/** Hidden on the lock screen: the console only exists once the app is unlocked. */
function ConsoleButton() {
  const consoleLog = useOptionalConsole();
  if (consoleLog === null) {
    return null;
  }
  const { unseenErrors, isPanelOpen, togglePanel } = consoleLog;
  const unseenLabel = plural(
    unseenErrors,
    consoleText("console.unseenErrors.one"),
    consoleText("console.unseenErrors.other"),
  );
  return (
    <button
      type="button"
      className={isPanelOpen ? "status-console active" : "status-console"}
      aria-expanded={isPanelOpen}
      title={unseenErrors > 0 ? unseenLabel : consoleText("console.buttonTitle")}
      onClick={togglePanel}
    >
      {consoleText("console.button")}
      {unseenErrors > 0 && (
        <span className="console-badge" aria-label={unseenLabel}>
          {unseenErrors}
        </span>
      )}
    </button>
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
      return t("statusBar.engineLoading");
    case "failed":
      return t("statusBar.engineFailed");
    case "ready":
      return plural(
        engine.moduleCount,
        t("statusBar.engineReady.one"),
        t("statusBar.engineReady.other"),
      );
  }
}

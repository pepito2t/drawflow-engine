import { useConsoleFeed } from "../hooks/console-context";
import { useLanguage } from "../hooks/use-language";
import { clearConsole, closeCurrentWindow } from "../lib/tauri/console";
import { ConsolePanel } from "./ConsolePanel";

/**
 * The detached console window: it only reads the shared log. It needs no lock screen of its own,
 * since the bridge opens it and serves the log only once the app is unlocked.
 */
export function ConsoleWindow() {
  useLanguage();
  const { state } = useConsoleFeed();
  return (
    <div className="console-window">
      <ConsolePanel
        entries={state.entries}
        loadError={state.loadError}
        onClose={() => {
          closeCurrentWindow().catch((error: unknown) => {
            console.error("Fermeture de la console impossible :", error);
          });
        }}
        onClear={clearConsole}
      />
    </div>
  );
}

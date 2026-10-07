import { useCallback, useEffect, useRef } from "react";
import { t } from "../i18n/console";
import { COMMANDS } from "../lib/commands";
import { recentErrors } from "../lib/console";
import { bringToFront } from "../lib/tauri/window";
import { useCommand } from "./command-registry";
import { copyForSupport, useConsole } from "./console-context";

/** Console commands, reachable from the status bar, the Stream Dock and the local API alike. */
export function useConsoleCommands(): void {
  const { entries, togglePanel, detach } = useConsole();
  const entriesRef = useRef(entries);
  useEffect(() => {
    entriesRef.current = entries;
  }, [entries]);

  const toggle = useCallback(async () => {
    togglePanel();
    await bringToFront();
  }, [togglePanel]);
  useCommand(COMMANDS.toggleConsole, toggle);

  useCommand(COMMANDS.detachConsole, detach);

  const copyErrors = useCallback(async () => {
    const errors = recentErrors(entriesRef.current);
    if (errors.length === 0) {
      throw new Error(t("console.noErrors"));
    }
    await copyForSupport(errors);
    return { copied: errors.length };
  }, []);
  useCommand(COMMANDS.copyConsoleErrors, copyErrors);
}

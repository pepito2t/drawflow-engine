import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { z } from "zod";
import { consoleEntrySchema, type ConsoleDraft, type ConsoleEntry } from "../console";

const ENTRY_EVENT = "console-entry";
const CLEARED_EVENT = "console-cleared";
const CONSOLE_VIEW_HASH = "#console";

/**
 * Fire-and-forget, and deliberately not through the logging `invoke` wrapper: a failure to log
 * must never produce another log entry.
 */
export function recordConsoleEntry(draft: ConsoleDraft): void {
  invoke("console_append", { entry: draft }).catch((error: unknown) => {
    console.error("Entrée de console non enregistrée :", error);
  });
}

export async function listConsoleEntries(): Promise<ConsoleEntry[]> {
  return z.array(consoleEntrySchema).parse(await invoke("console_entries"));
}

export function clearConsole(): Promise<void> {
  return invoke<undefined>("console_clear");
}

export function openConsoleWindow(): Promise<void> {
  return invoke<undefined>("console_open_window");
}

export interface ConsoleListeners {
  onEntry: (entry: ConsoleEntry) => void;
  onCleared: () => void;
  onInvalid: (error: unknown) => void;
}

export async function listenToConsole({
  onEntry,
  onCleared,
  onInvalid,
}: ConsoleListeners): Promise<() => void> {
  const stopEntries = await listen<unknown>(ENTRY_EVENT, ({ payload }) => {
    const parsed = consoleEntrySchema.safeParse(payload);
    if (parsed.success) {
      onEntry(parsed.data);
    } else {
      onInvalid(parsed.error);
    }
  });
  const stopCleared = await listen(CLEARED_EVENT, onCleared);
  return () => {
    stopEntries();
    stopCleared();
  };
}

/** Native clipboard: the web API refuses to write when the window is not focused (Stream Dock). */
export function copyToClipboard(text: string): Promise<void> {
  return writeText(text);
}

export function isConsoleWindow(): boolean {
  return window.location.hash === CONSOLE_VIEW_HASH;
}

export function closeCurrentWindow(): Promise<void> {
  return getCurrentWindow().close();
}

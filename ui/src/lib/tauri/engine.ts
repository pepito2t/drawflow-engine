import { invoke } from "./invoke";
import { t } from "../../i18n/shell";
import type { EngineMessageHandler, InvalidMessageHandler } from "../engine-message";
import { engineFailureDraft } from "../console-capture";
import { EngineCommandError, unwrapEngineOutput } from "../engine-output";
import type { FormValues } from "../form-schema";
import { parseBridgeError, translateBridgeError } from "./bridge-error";
import { recordConsoleEntry } from "./console";
import { engineChannel } from "./engine-channel";

/** A failed one-shot engine command is reported to the console before reaching the caller. */
function unwrapLogged(request: string, raw: unknown): string {
  try {
    return unwrapEngineOutput(raw);
  } catch (error: unknown) {
    if (error instanceof EngineCommandError) {
      recordConsoleEntry(engineFailureDraft(request, error));
    }
    throw error;
  }
}

export async function listModules(): Promise<string> {
  return unwrapLogged("list-modules", await invoke("list_modules"));
}

export async function getSettings(): Promise<string> {
  return unwrapLogged("settings.get", await invoke("get_settings"));
}

export async function saveSettings(values: Record<string, FormValues>): Promise<string> {
  return unwrapLogged("settings.set", await invoke("save_settings", { values }));
}

export type EngineRequestName =
  | "presets.list"
  | "presets.save"
  | "presets.remove"
  | "templates.list"
  | "templates.import"
  | "templates.remove"
  | "templates.set-default"
  | "settings.export"
  | "settings.read-import"
  | "profile.export"
  | "profile.read-import"
  | "profile.import"
  | "assistant.models"
  | "assistant.history-get"
  | "assistant.history-save"
  | "assistant.catalog"
  | "assistant.model-delete"
  | "help.guide"
  | "setup.scan"
  | "settings.add-synonyms"
  | "history.list"
  | "history.remove"
  | "history.clear"
  | "history.stats"
  | "mail.status"
  | "mail.connect-start"
  | "mail.connect-finish"
  | "mail.disconnect"
  | "mail.fetch"
  | "mail.list"
  | "mail.read"
  | "mail.export"
  | "mail.remove";

export async function engineRequest(
  request: EngineRequestName,
  payload: Record<string, unknown> = {},
): Promise<string> {
  return unwrapLogged(request, await invoke("engine_request", { request, payload }));
}

export function runModule(
  moduleId: string,
  inputs: FormValues,
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): Promise<string> {
  const onEvent = engineChannel(onMessage, onInvalid, { source: "engine", module: moduleId });
  return invoke<string>("run_module", { moduleId, inputs, onEvent });
}

export function cancelRun(runId: string): Promise<void> {
  return invoke<undefined>("cancel_run", { runId });
}

/** Tauri plugins still reject with plain strings: those are shown as they are. */
export function describeBridgeError(error: unknown): string {
  if (typeof error === "string") {
    return error;
  }
  const bridgeError = parseBridgeError(error);
  if (bridgeError) {
    return translateBridgeError(bridgeError);
  }
  return error instanceof Error ? error.message : t("bridge.unknownError");
}

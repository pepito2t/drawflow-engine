import { invoke } from "@tauri-apps/api/core";
import { t } from "../../i18n/shell";
import type { EngineMessageHandler, InvalidMessageHandler } from "../engine-message";
import { unwrapEngineOutput } from "../engine-output";
import type { FormValues } from "../form-schema";
import { engineChannel } from "./engine-channel";

export async function listModules(): Promise<string> {
  return unwrapEngineOutput(await invoke("list_modules"));
}

export async function getSettings(): Promise<string> {
  return unwrapEngineOutput(await invoke("get_settings"));
}

export async function saveSettings(values: Record<string, FormValues>): Promise<string> {
  return unwrapEngineOutput(await invoke("save_settings", { values }));
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
  return unwrapEngineOutput(await invoke("engine_request", { request, payload }));
}

export function runModule(
  moduleId: string,
  inputs: FormValues,
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): Promise<string> {
  const onEvent = engineChannel(onMessage, onInvalid);
  return invoke<string>("run_module", { moduleId, inputs, onEvent });
}

export function cancelRun(runId: string): Promise<void> {
  return invoke<undefined>("cancel_run", { runId });
}

export function describeBridgeError(error: unknown): string {
  if (typeof error === "string") {
    return error;
  }
  return error instanceof Error ? error.message : t("bridge.unknownError");
}

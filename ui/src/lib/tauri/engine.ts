import { Channel, invoke } from "@tauri-apps/api/core";
import { engineMessageSchema, type EngineMessage } from "../engine-message";
import type { FormValues } from "../form-schema";

export function listModules(): Promise<string> {
  return invoke<string>("list_modules");
}

export function runModule(
  moduleId: string,
  inputs: FormValues,
  onMessage: (message: EngineMessage) => void,
): Promise<void> {
  const channel = new Channel<unknown>((raw) => {
    onMessage(engineMessageSchema.parse(raw));
  });
  return invoke<undefined>("run_module", { moduleId, inputs, onEvent: channel });
}

export function cancelRun(): Promise<void> {
  return invoke<undefined>("cancel_run");
}

export function describeBridgeError(error: unknown): string {
  if (typeof error === "string") {
    return error;
  }
  return error instanceof Error ? error.message : "Erreur de communication avec le moteur.";
}

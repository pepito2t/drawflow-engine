import { Channel, invoke } from "@tauri-apps/api/core";
import { engineMessageSchema, type EngineMessage } from "../engine-message";
import type { EngineSetupAction } from "../setup";
import { engineRequest } from "./engine";

export function scanSetup(): Promise<string> {
  return engineRequest("setup.scan");
}

export function runSetupAction(
  action: EngineSetupAction,
  onMessage: (message: EngineMessage) => void,
): Promise<string> {
  const channel = new Channel<unknown>((raw) => {
    onMessage(engineMessageSchema.parse(raw));
  });
  return invoke<string>("run_setup_action", { action, onEvent: channel });
}

export function openDownloadPage(url: string): Promise<void> {
  return invoke<undefined>("open_download_page", { url });
}

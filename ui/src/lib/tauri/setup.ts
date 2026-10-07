import { invoke } from "./invoke";
import type { EngineMessageHandler, InvalidMessageHandler } from "../engine-message";
import type { EngineSetupAction } from "../setup";
import { engineRequest } from "./engine";
import { engineChannel } from "./engine-channel";

export function scanSetup(): Promise<string> {
  return engineRequest("setup.scan");
}

export function runSetupAction(
  action: EngineSetupAction,
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): Promise<string> {
  const onEvent = engineChannel(onMessage, onInvalid, { source: "setup", module: action });
  return invoke<string>("run_setup_action", { action, onEvent });
}

export function openDownloadPage(url: string): Promise<void> {
  return invoke<undefined>("open_download_page", { url });
}

import { invoke } from "./invoke";
import { getCurrentWindow } from "@tauri-apps/api/window";

export async function bringToFront(): Promise<void> {
  const window = getCurrentWindow();
  await window.unminimize();
  await window.show();
  await window.setFocus();
}

export function openOutput(path: string): Promise<void> {
  return invoke<undefined>("open_output", { path });
}

export function openLogsFolder(): Promise<void> {
  return invoke<undefined>("open_logs_folder");
}

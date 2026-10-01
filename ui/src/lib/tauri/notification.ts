import { getCurrentWindow } from "@tauri-apps/api/window";
import {
  isPermissionGranted,
  requestPermission,
  sendNotification,
} from "@tauri-apps/plugin-notification";

export function isWindowFocused(): Promise<boolean> {
  return getCurrentWindow().isFocused();
}

export async function notify(title: string, body: string): Promise<void> {
  const granted = (await isPermissionGranted()) || (await requestPermission()) === "granted";
  if (granted) {
    sendNotification({ title, body });
  }
}

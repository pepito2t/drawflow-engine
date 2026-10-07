import { invoke } from "@tauri-apps/api/core";
import { relaunch } from "@tauri-apps/plugin-process";
import { check } from "@tauri-apps/plugin-updater";
import { z } from "zod";

export interface AvailableUpdate {
  version: string;
  install: (onProgress: (downloaded: number, total: number | null) => void) => Promise<void>;
}

export async function isUpdaterConfigured(): Promise<boolean> {
  return z.boolean().parse(await invoke("updater_configured"));
}

export async function findUpdate(): Promise<AvailableUpdate | null> {
  const update = await check();
  if (update === null) {
    return null;
  }
  return {
    version: update.version,
    install: async (onProgress) => {
      let downloaded = 0;
      let total: number | null = null;
      await update.download((event) => {
        if (event.event === "Started") {
          total = event.data.contentLength ?? null;
        } else if (event.event === "Progress") {
          downloaded += event.data.chunkLength;
          onProgress(downloaded, total);
        }
      });
      // The installer replaces the sidecar: nothing from the engine may still run at that point.
      await invoke("prepare_for_update");
      await update.install();
      await relaunch();
    },
  };
}

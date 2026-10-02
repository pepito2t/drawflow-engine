import { useCallback, useEffect, useRef } from "react";
import type { CatalogModule } from "../lib/catalog";
import { COMMANDS } from "../lib/commands";
import { entryFor, runningModuleIds } from "../lib/runs-store";
import { cancelRun } from "../lib/tauri/engine";
import { bringToFront, openOutput } from "../lib/tauri/window";
import { useCommand } from "./command-registry";
import { useNotificationCenter } from "./notification-center";
import { usePresets } from "./presets-context";
import { useRunsStore } from "./runs-context";

interface AppCommandTargets {
  modules: CatalogModule[];
  selectModule: (moduleId: string) => void;
  openSettings: () => void;
}

/** Registers the app-level commands shared by the UI, the Stream Deck and future integrations. */
export function useAppCommands({ modules, selectModule, openSettings }: AppCommandTargets): void {
  const { state, dispatch } = useRunsStore();
  const { presets } = usePresets();
  const { publish, subscribe } = useNotificationCenter();
  const lastOutput = useRef<string | null>(null);

  useEffect(
    () =>
      subscribe((event) => {
        const output = event.type === "runFinished" ? event.outputs.at(-1) : undefined;
        if (output) {
          lastOutput.current = output;
        }
      }),
    [subscribe],
  );

  const openTab = useCallback(
    async ({ moduleId }: { moduleId: string }) => {
      if (!modules.some((module) => module.manifest.id === moduleId)) {
        throw new Error(`Fonctionnalité inconnue : ${moduleId}`);
      }
      selectModule(moduleId);
      await bringToFront();
    },
    [modules, selectModule],
  );
  useCommand(COMMANDS.openTab, openTab);

  const runPreset = useCallback(
    async ({ presetId }: { presetId: string }) => {
      const preset = presets.find((candidate) => candidate.id === presetId);
      if (!preset) {
        throw new Error("Ce préréglage n'existe plus.");
      }
      if (entryFor(state, preset.module).run.status === "running") {
        throw new Error("Cette fonctionnalité est déjà en cours d'exécution.");
      }
      await openTab({ moduleId: preset.module });
      publish({ type: "presetRunRequested", presetId, moduleId: preset.module });
    },
    [presets, state, openTab, publish],
  );
  useCommand(COMMANDS.runPreset, runPreset);

  const cancelAll = useCallback(async () => {
    const running = runningModuleIds(state)
      .map((moduleId) => ({ moduleId, runId: entryFor(state, moduleId).runId }))
      .filter((run): run is { moduleId: string; runId: string } => run.runId !== null);
    for (const run of running) {
      dispatch({ type: "run", moduleId: run.moduleId, action: { type: "cancelRequested" } });
    }
    await Promise.all(running.map((run) => cancelRun(run.runId)));
  }, [state, dispatch]);
  useCommand(COMMANDS.cancelAllRuns, cancelAll);

  const openLastResult = useCallback(async () => {
    if (lastOutput.current === null) {
      throw new Error("Aucun fichier produit depuis l'ouverture de l'application.");
    }
    await openOutput(lastOutput.current);
  }, []);
  useCommand(COMMANDS.openLastResult, openLastResult);

  const settings = useCallback(async () => {
    openSettings();
    await bringToFront();
  }, [openSettings]);
  useCommand(COMMANDS.openSettings, settings);
}

import { useCallback, useEffect, useRef } from "react";
import type { CatalogModule } from "../lib/catalog";
import { COMMANDS } from "../lib/commands";
import { entryFor, runningModuleIds } from "../lib/runs-store";
import { cancelRun } from "../lib/tauri/engine";
import { listHistory } from "../lib/tauri/history";
import { bringToFront, openOutput } from "../lib/tauri/window";
import { AI_MODELS_TAB_ID, SETUP_TAB_ID } from "../lib/setup";
import { useCommand } from "./command-registry";
import { useNotificationCenter } from "./notification-center";
import { usePresets } from "./presets-context";
import { useRunsStore } from "./runs-context";

interface AppCommandTargets {
  modules: CatalogModule[];
  selectModule: (moduleId: string) => void;
  openSettings: (tab?: string) => void;
  toggleAssistant: () => void;
  openHelp: (topic?: string) => void;
  openHistory: () => void;
  openToday: () => void;
}

/** Registers the app-level commands shared by the UI, the Stream Dock and future integrations. */
export function useAppCommands({
  modules,
  selectModule,
  openSettings,
  toggleAssistant,
  openHelp,
  openHistory,
  openToday,
}: AppCommandTargets): void {
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

  const runFeature = useCallback(
    async ({ moduleId, inputs }: { moduleId: string; inputs: Record<string, unknown> }) => {
      if (entryFor(state, moduleId).run.status === "running") {
        throw new Error("Cette fonctionnalité est déjà en cours d'exécution.");
      }
      await openTab({ moduleId });
      publish({ type: "featureRunRequested", moduleId, inputs });
    },
    [state, openTab, publish],
  );
  useCommand(COMMANDS.runFeature, runFeature);

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

  useCommand(COMMANDS.openHistory, openHistory);
  useCommand(COMMANDS.openToday, openToday);

  const rerunHistory = useCallback(
    async ({ entryId }: { entryId: string }) => {
      const entry = (await listHistory()).find((candidate) => candidate.id === entryId);
      if (!entry) {
        throw new Error("Ce traitement n'est plus dans l'historique.");
      }
      await runFeature({ moduleId: entry.module, inputs: entry.inputs });
    },
    [runFeature],
  );
  useCommand(COMMANDS.rerunHistory, rerunHistory);

  const appState = useCallback(
    () => ({
      modules: modules.map(({ manifest }) => ({
        id: manifest.id,
        name: manifest.name,
        icon: manifest.icon,
      })),
      presets: presets.map(({ id, name, module }) => ({ id, name, module })),
      runs: Object.entries(state).map(([moduleId, entry]) => ({
        moduleId,
        status: entry.run.status,
        current: entry.run.progress?.current ?? null,
        total: entry.run.progress?.total ?? null,
      })),
    }),
    [modules, presets, state],
  );
  useCommand(COMMANDS.appState, appState);

  const settings = useCallback(async () => {
    openSettings();
    await bringToFront();
  }, [openSettings]);
  useCommand(COMMANDS.openSettings, settings);

  const assistant = useCallback(async () => {
    toggleAssistant();
    await bringToFront();
  }, [toggleAssistant]);
  useCommand(COMMANDS.toggleAssistant, assistant);

  const setup = useCallback(async () => {
    openSettings(SETUP_TAB_ID);
    await bringToFront();
  }, [openSettings]);
  useCommand(COMMANDS.openSetup, setup);

  const aiModels = useCallback(async () => {
    openSettings(AI_MODELS_TAB_ID);
    await bringToFront();
  }, [openSettings]);
  useCommand(COMMANDS.openModels, aiModels);

  const helpCommand = useCallback(
    async ({ topic }: { topic?: string | undefined }) => {
      openHelp(topic);
      await bringToFront();
    },
    [openHelp],
  );
  useCommand(COMMANDS.openHelp, helpCommand);
}

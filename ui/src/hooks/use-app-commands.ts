import { t } from "../i18n/shell";
import { useCallback, useEffect, useRef } from "react";
import type { CatalogModule } from "../lib/catalog";
import { COMMANDS } from "../lib/commands";
import { entryFor, runningModuleIds } from "../lib/runs-store";
import { engineRequest } from "../lib/tauri/engine";
import { listHistory } from "../lib/tauri/history";
import { fetchMail } from "../lib/tauri/mail";
import { getAutomationStatus } from "../lib/tauri/automations";
import { inputsForNewFile } from "../lib/automations";
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
  openMail: () => void;
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
  openMail,
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
        throw new Error(t("appCommands.unknownFeature", { id: moduleId }));
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
        throw new Error(t("appCommands.presetGone"));
      }
      if (entryFor(state, preset.module).run.status === "running") {
        throw new Error(t("appCommands.alreadyRunning"));
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
        throw new Error(t("appCommands.alreadyRunning"));
      }
      await openTab({ moduleId });
      publish({ type: "featureRunRequested", moduleId, inputs });
    },
    [state, openTab, publish],
  );
  useCommand(COMMANDS.runFeature, runFeature);

  const cancelAll = useCallback(() => {
    for (const moduleId of runningModuleIds(state)) {
      if (!entryFor(state, moduleId).run.cancelRequested) {
        dispatch({ type: "run", moduleId, action: { type: "cancelRequested" } });
      }
    }
    return Promise.resolve();
  }, [state, dispatch]);
  useCommand(COMMANDS.cancelAllRuns, cancelAll);

  const openLastResult = useCallback(async () => {
    if (lastOutput.current === null) {
      throw new Error(t("appCommands.noOutputYet"));
    }
    await openOutput(lastOutput.current);
  }, []);
  useCommand(COMMANDS.openLastResult, openLastResult);

  const addSynonyms = useCallback(
    async ({ columns }: { columns: Record<string, string[]> }) => {
      await engineRequest("settings.add-synonyms", { columns });
      publish({ type: "settingsSaved" });
    },
    [publish],
  );
  useCommand(COMMANDS.addSynonyms, addSynonyms);

  useCommand(COMMANDS.openHistory, openHistory);
  useCommand(COMMANDS.openToday, openToday);
  useCommand(COMMANDS.openMail, openMail);

  const fetchMailbox = useCallback(async () => {
    const result = await fetchMail();
    publish({ type: "mailFetched", added: result.added });
    return result;
  }, [publish]);
  useCommand(COMMANDS.fetchMail, fetchMailbox);

  const rerunHistory = useCallback(
    async ({ entryId }: { entryId: string }) => {
      const entry = (await listHistory()).find((candidate) => candidate.id === entryId);
      if (!entry) {
        throw new Error(t("appCommands.historyEntryGone"));
      }
      await runFeature({ moduleId: entry.module, inputs: entry.inputs });
    },
    [runFeature],
  );
  useCommand(COMMANDS.rerunHistory, rerunHistory);

  const runAutomation = useCallback(
    async ({ automationId, path }: { automationId: string; path: string }) => {
      const { automations } = await getAutomationStatus();
      const automation = automations.find((candidate) => candidate.id === automationId);
      const preset = presets.find((candidate) => candidate.id === automation?.presetId);
      const module = modules.find((candidate) => candidate.manifest.id === preset?.module);
      if (!automation?.enabled || !preset || !module) {
        throw new Error(t("appCommands.automationGone"));
      }
      await runFeature({
        moduleId: module.manifest.id,
        inputs: inputsForNewFile(module.fields, preset.inputs, path),
      });
    },
    [modules, presets, runFeature],
  );
  useCommand(COMMANDS.runAutomation, runAutomation);

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

import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { COMMANDS } from "../lib/commands";
import { cancelledRunIds, fakeRuns, resetFakeEngine } from "../lib/tauri/__mocks__/engine";
import { openedOutputs } from "../lib/tauri/__mocks__/window";
import { catalogModule, TestProviders, useRecordedEvents } from "../test/providers";
import { useCommands } from "./command-registry";
import { useNotificationCenter } from "./notification-center";
import { useAppCommands } from "./use-app-commands";
import { useModuleRun } from "./use-module-run";

vi.mock("../lib/tauri/engine");
vi.mock("../lib/tauri/window");

const MODULES = [catalogModule("parts"), catalogModule("diff")];

function renderAppCommands() {
  const calls: string[] = [];
  const rendered = renderHook(
    () => {
      useAppCommands({
        modules: MODULES,
        selectModule: (moduleId) => calls.push(`select:${moduleId}`),
        openSettings: (tab) => calls.push(`settings:${tab ?? ""}`),
        toggleAssistant: () => calls.push("assistant"),
        openHelp: (topic) => calls.push(`help:${topic ?? ""}`),
        openHistory: () => calls.push("history"),
        openToday: () => calls.push("today"),
        openMail: () => calls.push("mail"),
      });
      return {
        commands: useCommands(),
        center: useNotificationCenter(),
        run: useModuleRun("parts"),
        events: useRecordedEvents(),
      };
    },
    { wrapper: TestProviders },
  );
  return { ...rendered, calls };
}

async function settle(): Promise<void> {
  await act(async () => {
    await Promise.resolve();
  });
}

describe("useAppCommands", () => {
  beforeEach(() => {
    resetFakeEngine();
    openedOutputs.length = 0;
  });

  it("opens a known feature tab and refuses an unknown one", async () => {
    const { result, calls } = renderAppCommands();

    expect(await result.current.commands.execute(COMMANDS.openTab, { moduleId: "diff" })).toEqual({
      ok: true,
    });
    const unknown = await result.current.commands.execute(COMMANDS.openTab, { moduleId: "x" });

    expect(calls).toEqual(["select:diff"]);
    expect(unknown.ok).toBe(false);
  });

  it("asks the feature's workspace to run with the given inputs", async () => {
    const { result, calls } = renderAppCommands();

    await act(() =>
      result.current.commands.execute(COMMANDS.runFeature, {
        moduleId: "parts",
        inputs: { name: "Nord" },
      }),
    );

    expect(calls).toEqual(["select:parts"]);
    expect(result.current.events).toContainEqual({
      type: "featureRunRequested",
      moduleId: "parts",
      inputs: { name: "Nord" },
    });
  });

  it("refuses to start a feature that is already running", async () => {
    const { result } = renderAppCommands();
    act(() => {
      result.current.run.start({ name: "Nord" });
    });
    await settle();

    const outcome = await result.current.commands.execute(COMMANDS.runFeature, {
      moduleId: "parts",
      inputs: {},
    });

    expect(outcome.ok).toBe(false);
  });

  it("cancels every running treatment", async () => {
    const { result } = renderAppCommands();
    act(() => {
      result.current.run.start({ name: "Nord" });
    });
    await settle();

    await act(() => result.current.commands.execute(COMMANDS.cancelAllRuns));
    await settle();

    expect(result.current.run.state.cancelRequested).toBe(true);
    expect(cancelledRunIds).toEqual([fakeRuns[0]?.runId]);
  });

  it("describes the modules and the runs in the app state", async () => {
    const { result } = renderAppCommands();
    act(() => {
      result.current.run.start({ name: "Nord" });
    });
    await settle();

    const outcome = await result.current.commands.execute(COMMANDS.appState);

    expect(outcome).toMatchObject({
      ok: true,
      data: {
        modules: [{ id: "parts" }, { id: "diff" }],
        runs: [{ moduleId: "parts", status: "running" }],
      },
    });
  });

  it("opens the last output of a finished run, and explains when there is none", async () => {
    const { result } = renderAppCommands();

    expect((await result.current.commands.execute(COMMANDS.openLastResult)).ok).toBe(false);
    act(() => {
      result.current.center.publish({
        type: "runFinished",
        moduleId: "parts",
        moduleName: "Module parts",
        outcome: "succeeded",
        message: "ok",
        durationMs: 1,
        outputs: ["C:\\out\\liste.xlsx"],
      });
    });

    expect((await result.current.commands.execute(COMMANDS.openLastResult)).ok).toBe(true);
    expect(openedOutputs).toEqual(["C:\\out\\liste.xlsx"]);
  });

  it("routes the settings, help and assistant commands to their screens", async () => {
    const { result, calls } = renderAppCommands();

    await result.current.commands.execute(COMMANDS.openSettings);
    await result.current.commands.execute(COMMANDS.openHelp, { topic: "dwg" });
    await result.current.commands.execute(COMMANDS.toggleAssistant);

    expect(calls).toEqual(["settings:", "help:dwg", "assistant"]);
  });
});

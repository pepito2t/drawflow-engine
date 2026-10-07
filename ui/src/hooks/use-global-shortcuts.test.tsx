import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ModuleWorkspace } from "../components/ModuleWorkspace";
import { COMMANDS } from "../lib/commands";
import { fakeRuns, resetFakeEngine } from "../lib/tauri/__mocks__/engine";
import { catalogModule, TestProviders } from "../test/providers";
import { CommandProvider, useCommand } from "./command-registry";
import { useAppCommands } from "./use-app-commands";
import { useGlobalShortcuts } from "./use-global-shortcuts";

vi.mock("../lib/tauri/engine");
vi.mock("../lib/tauri/dialog");
vi.mock("../lib/tauri/drag-drop");
vi.mock("../lib/tauri/window");

const MODULE = catalogModule("parts");

function renderShortcuts(opened: string[]) {
  return renderHook(
    () => {
      useCommand(COMMANDS.openSettings, () => {
        opened.push("settings");
      });
      useCommand(COMMANDS.openHelp, () => {
        opened.push("help");
      });
      useGlobalShortcuts();
    },
    { wrapper: CommandProvider },
  );
}

async function pressOn(target: Element, key: string, ctrlKey = false): Promise<void> {
  await act(async () => {
    fireEvent.keyDown(target, { key, ctrlKey });
    await Promise.resolve();
  });
}

function ShortcutApp() {
  useAppCommands({
    modules: [MODULE],
    selectedId: "parts",
    selectModule: () => undefined,
    openSettings: () => undefined,
    toggleAssistant: () => undefined,
    openHelp: () => undefined,
    openHistory: () => undefined,
    openToday: () => undefined,
    openMail: () => undefined,
  });
  useGlobalShortcuts();
  return <ModuleWorkspace module={MODULE} />;
}

describe("useGlobalShortcuts", () => {
  beforeEach(() => {
    resetFakeEngine();
  });

  it("opens the settings with Ctrl+, and the help with F1", async () => {
    const opened: string[] = [];
    renderShortcuts(opened);

    await pressOn(document.body, ",", true);
    await pressOn(document.body, "F1");

    expect(opened).toEqual(["settings", "help"]);
  });

  it("does nothing from inside an open dialog", async () => {
    const opened: string[] = [];
    renderShortcuts(opened);
    const dialog = document.createElement("dialog");
    dialog.open = true;
    document.body.append(dialog);

    await pressOn(dialog, ",", true);

    expect(opened).toEqual([]);
    dialog.remove();
  });

  it("runs the feature on screen with Ctrl+Enter, with the values typed in its form", async () => {
    render(
      <TestProviders>
        <ShortcutApp />
      </TestProviders>,
    );
    const name = screen.getByLabelText(/Nom/);
    fireEvent.change(name, { target: { value: "Façade sud" } });

    await pressOn(name, "Enter", true);

    expect(fakeRuns.map((run) => run.inputs)).toEqual([{ name: "Façade sud" }]);
  });

  it("does not run a feature whose required fields are empty", async () => {
    render(
      <TestProviders>
        <ShortcutApp />
      </TestProviders>,
    );

    await pressOn(document.body, "Enter", true);

    expect(fakeRuns).toEqual([]);
  });
});

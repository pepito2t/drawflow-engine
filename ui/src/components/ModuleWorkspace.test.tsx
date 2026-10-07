import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  cancelledRunIds,
  engineEvent,
  exitMessage,
  fakeRuns,
  resetFakeEngine,
} from "../lib/tauri/__mocks__/engine";
import { catalogModule, TestProviders } from "../test/providers";
import { ModuleWorkspace } from "./ModuleWorkspace";

vi.mock("../lib/tauri/engine");
vi.mock("../lib/tauri/dialog");
vi.mock("../lib/tauri/drag-drop");
vi.mock("../lib/tauri/window");

function renderWorkspace() {
  render(
    <TestProviders>
      <ModuleWorkspace module={catalogModule("parts")} />
    </TestProviders>,
  );
}

async function startRun() {
  fireEvent.change(screen.getByLabelText(/Nom/), { target: { value: "Façade nord" } });
  fireEvent.click(screen.getByRole("button", { name: "Lancer" }));
  await act(async () => {
    await Promise.resolve();
  });
  const run = fakeRuns.at(-1);
  if (!run) {
    throw new Error("Aucun traitement lancé.");
  }
  return run;
}

describe("ModuleWorkspace", () => {
  beforeEach(() => {
    resetFakeEngine();
  });

  it("keeps Lancer disabled while a required field is empty", () => {
    renderWorkspace();

    expect(screen.getByRole("button", { name: "Lancer" })).toHaveProperty("disabled", true);
    expect(screen.getByText(/À renseigner avant de lancer : Nom/)).toBeTruthy();
  });

  it("runs the module with the form values, shows progress then the result", async () => {
    renderWorkspace();

    const run = await startRun();
    expect(run.moduleId).toBe("parts");
    expect(run.inputs).toEqual({ name: "Façade nord" });

    act(() => {
      run.emit(engineEvent({ type: "progress", current: 1, total: 4, message: "a.dwg" }));
    });
    const progress = screen.getByRole("progressbar");
    expect(progress.getAttribute("value")).toBe("1");
    expect(progress.getAttribute("max")).toBe("4");

    act(() => {
      run.emit(engineEvent({ type: "result", summary: "12 pièces", outputs: ["C:\\out.xlsx"] }));
      run.emit(exitMessage(0));
    });
    expect(screen.getByRole("status").textContent).toContain("12 pièces");
    expect(screen.getByText("C:\\out.xlsx")).toBeTruthy();
    expect(screen.queryByRole("progressbar")).toBeNull();
  });

  it("cancels a running treatment and reports it as cancelled", async () => {
    renderWorkspace();
    const run = await startRun();

    fireEvent.click(screen.getByRole("button", { name: "Annuler" }));
    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByRole("button", { name: "Annulation…" })).toHaveProperty("disabled", true);
    expect(cancelledRunIds).toEqual([run.runId]);

    act(() => {
      run.emit(exitMessage(null));
    });
    expect(screen.getByRole("button", { name: "Lancer" })).toHaveProperty("disabled", false);
    expect(screen.getAllByText(/annulé/i).length).toBeGreaterThan(0);
  });

  it("shows the engine error when the treatment fails", async () => {
    renderWorkspace();
    const run = await startRun();

    act(() => {
      run.emit(
        engineEvent({
          type: "error",
          message: "Fichier illisible",
          file: "a.dwg",
          hint: "Vérifier le fichier",
        }),
      );
      run.emit(exitMessage(1));
    });

    expect(screen.getByText("Le traitement a échoué")).toBeTruthy();
    expect(screen.getAllByText("Fichier illisible").length).toBeGreaterThan(0);
  });
});

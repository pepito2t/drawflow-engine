import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { Profiler } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { engineEvent, fakeRuns, resetFakeEngine } from "../lib/tauri/__mocks__/engine";
import { catalogModule, TestProviders } from "../test/providers";
import { ModuleTabs } from "./ModuleTabs";
import { ModuleWorkspace } from "./ModuleWorkspace";
import { RUN_LOG_VISIBLE_LINES } from "./RunPanel";

vi.mock("../lib/tauri/engine");
vi.mock("../lib/tauri/dialog");
vi.mock("../lib/tauri/drag-drop");
vi.mock("../lib/tauri/window");

const EMITTED_MESSAGES = 600;
const MODULES = [catalogModule("busy"), catalogModule("idle")];

function renderTwoWorkspaces(renders: Map<string, number>) {
  const count = (id: string) => {
    renders.set(id, (renders.get(id) ?? 0) + 1);
  };
  render(
    <TestProviders>
      <Profiler id="tabs" onRender={count}>
        <ModuleTabs
          modules={MODULES}
          leadingTabs={[]}
          extraTabs={[]}
          selectedId="busy"
          onSelect={() => undefined}
          footer={null}
        />
      </Profiler>
      {MODULES.map((module) => (
        <section key={module.manifest.id} data-testid={module.manifest.id}>
          <Profiler id={module.manifest.id} onRender={count}>
            <ModuleWorkspace module={module} />
          </Profiler>
        </section>
      ))}
    </TestProviders>,
  );
}

describe("rendering during a run", () => {
  beforeEach(() => {
    resetFakeEngine();
  });

  it("re-renders only the workspace whose treatment emits", async () => {
    const renders = new Map<string, number>();
    renderTwoWorkspaces(renders);
    const busy = within(screen.getByTestId("busy"));
    fireEvent.change(busy.getByLabelText(/Nom/), { target: { value: "Nord" } });
    fireEvent.click(busy.getByRole("button", { name: "Lancer" }));
    await act(async () => {
      await Promise.resolve();
    });
    const run = fakeRuns[0];
    if (!run) throw new Error("Aucun traitement lancé.");
    const before = new Map(renders);

    for (let index = 1; index <= EMITTED_MESSAGES; index += 1) {
      act(() => {
        run.emit(
          engineEvent({ type: "progress", current: index, total: EMITTED_MESSAGES, message: "f" }),
        );
        run.emit(engineEvent({ type: "log", message: `ligne ${String(index)}` }));
      });
    }

    const delta = (id: string) => (renders.get(id) ?? 0) - (before.get(id) ?? 0);
    expect(delta("busy")).toBe(EMITTED_MESSAGES);
    expect(delta("idle")).toBe(0);
    expect(delta("tabs")).toBe(0);
  });

  it("keeps only the latest log lines in the page and says how many are hidden", async () => {
    renderTwoWorkspaces(new Map());
    const busy = within(screen.getByTestId("busy"));
    fireEvent.change(busy.getByLabelText(/Nom/), { target: { value: "Nord" } });
    fireEvent.click(busy.getByRole("button", { name: "Lancer" }));
    await act(async () => {
      await Promise.resolve();
    });

    act(() => {
      for (let index = 1; index <= EMITTED_MESSAGES; index += 1) {
        fakeRuns[0]?.emit(engineEvent({ type: "log", message: `ligne ${String(index)}` }));
      }
    });

    const hidden = EMITTED_MESSAGES - RUN_LOG_VISIBLE_LINES;
    expect(document.querySelectorAll(".log-entry")).toHaveLength(RUN_LOG_VISIBLE_LINES);
    expect(busy.getByText(`${String(hidden)} lignes plus anciennes masquées`)).toBeTruthy();
    expect(busy.getByText(`ligne ${String(EMITTED_MESSAGES)}`)).toBeTruthy();
    expect(busy.queryByText("ligne 1")).toBeNull();
  });
});

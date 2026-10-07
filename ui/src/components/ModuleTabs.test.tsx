import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { catalogModule, TestProviders } from "../test/providers";
import { ModuleTabs } from "./ModuleTabs";

vi.mock("../lib/tauri/engine");

const MODULES = [catalogModule("parts"), catalogModule("diff")];

function SelectableTabs() {
  const [selectedId, setSelectedId] = useState("today");
  return (
    <ModuleTabs
      modules={MODULES}
      leadingTabs={[{ id: "today", label: "Aujourd'hui", icon: null }]}
      extraTabs={[{ id: "history", label: "Historique", icon: null }]}
      selectedId={selectedId}
      onSelect={setSelectedId}
      footer={null}
    />
  );
}

function renderTabs() {
  render(
    <TestProviders>
      <SelectableTabs />
    </TestProviders>,
  );
}

const tab = (name: string) => screen.getByRole("tab", { name });
const press = (key: string) => {
  fireEvent.keyDown(screen.getByRole("tablist"), { key });
};

describe("ModuleTabs keyboard navigation", () => {
  it("leaves only the selected tab in the Tab order", () => {
    renderTabs();

    expect(tab("Aujourd'hui").tabIndex).toBe(0);
    expect(tab("Module parts").tabIndex).toBe(-1);
  });

  it("moves and selects with the arrows, Home and End, wrapping at the ends", () => {
    renderTabs();
    tab("Aujourd'hui").focus();

    press("ArrowDown");
    expect(document.activeElement).toBe(tab("Module parts"));
    expect(tab("Module parts").getAttribute("aria-selected")).toBe("true");

    press("End");
    expect(document.activeElement).toBe(tab("Historique"));

    press("ArrowDown");
    expect(document.activeElement).toBe(tab("Aujourd'hui"));

    press("ArrowUp");
    expect(document.activeElement).toBe(tab("Historique"));

    press("Home");
    expect(document.activeElement).toBe(tab("Aujourd'hui"));
    expect(tab("Aujourd'hui").getAttribute("aria-selected")).toBe("true");
  });
});

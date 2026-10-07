import { act, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsFeedProvider } from "../hooks/settings-feed";
import { resetFakeEngine, respondTo, setFakeSettings } from "../lib/tauri/__mocks__/engine";
import { TestProviders } from "../test/providers";
import { HelpDialog } from "./HelpDialog";
import { SettingsDialog } from "./SettingsDialog";

vi.mock("../lib/tauri/engine");
vi.mock("../lib/tauri/dialog");
vi.mock("../lib/tauri/drag-drop");
vi.mock("../lib/tauri/window");

const SETTINGS = {
  sections: [
    {
      id: "general",
      title: "Général",
      schema: { properties: { batch_size: { title: "Taille des lots", "x-ui": "text" } } },
      values: { batch_size: "8" },
      error: null,
    },
  ],
};

const GUIDE = {
  sections: [
    { id: "start", title: "Démarrer", markdown: "Bienvenue." },
    { id: "parts", title: "Liste de pièces", markdown: "Choisir les plans." },
  ],
};

function DialogLauncher({ kind }: { kind: "settings" | "help" }) {
  const [isOpen, setIsOpen] = useState(false);
  const close = () => {
    setIsOpen(false);
  };
  return (
    <>
      <button
        type="button"
        onClick={() => {
          setIsOpen(true);
        }}
      >
        Ouvrir
      </button>
      {isOpen && kind === "settings" && <SettingsDialog modules={[]} onClose={close} />}
      {isOpen && kind === "help" && <HelpDialog topic={undefined} onClose={close} />}
    </>
  );
}

async function openFrom(kind: "settings" | "help"): Promise<HTMLElement> {
  render(
    <TestProviders>
      <SettingsFeedProvider>
        <DialogLauncher kind={kind} />
      </SettingsFeedProvider>
    </TestProviders>,
  );
  const trigger = screen.getByRole("button", { name: "Ouvrir" });
  trigger.focus();
  await act(async () => {
    fireEvent.click(trigger);
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  return trigger;
}

const pressEscape = () => {
  fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
};

describe("dialogs", () => {
  beforeEach(() => {
    resetFakeEngine();
    setFakeSettings(JSON.stringify(SETTINGS));
    respondTo("help.guide", JSON.stringify(GUIDE));
  });

  it("opens the help as a modal and gives the focus back to its trigger on Escape", async () => {
    const trigger = await openFrom("help");

    const dialog = screen.getByRole("dialog", { name: "Aide" });
    expect(dialog).toHaveProperty("open", true);
    pressEscape();

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("closes the settings at once when nothing was edited", async () => {
    const trigger = await openFrom("settings");

    fireEvent.click(screen.getByRole("button", { name: "Fermer" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  it("asks before dropping unsaved settings, from Escape as from the close button", async () => {
    const trigger = await openFrom("settings");
    fireEvent.change(screen.getByLabelText("Taille des lots"), { target: { value: "4" } });

    pressEscape();
    expect(screen.getByRole("alert").textContent).toContain("ne sont pas enregistrées");
    pressEscape();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("dialog")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Fermer" }));
    fireEvent.click(screen.getByRole("button", { name: "Fermer sans enregistrer" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });
});

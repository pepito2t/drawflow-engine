import { describe, expect, it } from "vitest";
import {
  describeSystem,
  isEngineAction,
  missingCount,
  needsConfirmation,
  parseSetupReport,
  setupRunReducer,
  type SetupRun,
  type SetupRunMessage,
} from "./setup";

const REPORT = JSON.stringify({
  system: { os: "windows", arch: "amd64", package_manager: "winget" },
  items: [
    {
      id: "oda",
      label: "ODA File Converter",
      status: "missing",
      detail: "Nécessaire pour lire les fichiers DWG.",
      actions: [
        { id: "oda.install", label: "Installer", url: null },
        {
          id: "oda.open-page",
          label: "Page de téléchargement",
          url: "https://www.opendesign.com/guestfiles/oda_file_converter",
        },
      ],
    },
    {
      id: "stream-deck",
      label: "Plugin Stream Dock",
      status: "optional",
      detail: "Facultatif",
      actions: [{ id: "streamdock.install-plugin", label: "Installer le plugin", url: null }],
    },
  ],
});

const line = (event: object): SetupRunMessage => ({ kind: "line", line: JSON.stringify(event) });

function run(messages: SetupRunMessage[]): SetupRun {
  return messages.reduce(setupRunReducer, { status: "idle" });
}

describe("setup report", () => {
  it("counts only required items that are missing", () => {
    const report = parseSetupReport(REPORT);

    expect(missingCount(report)).toBe(1);
    expect(describeSystem(report)).toBe("Windows · amd64 · winget");
  });

  it("rejects an unexpected answer", () => {
    expect(() => parseSetupReport('{"items": 3}')).toThrow();
  });

  it("tells engine actions from pages and asks before installing third-party software", () => {
    expect(isEngineAction("oda.install")).toBe(true);
    expect(isEngineAction("oda.open-page")).toBe(false);
    expect(isEngineAction("streamdock.install-plugin")).toBe(true);
    expect(needsConfirmation("ollama.install")).toBe(true);
    expect(needsConfirmation("oda.use-detected")).toBe(false);
  });
});

describe("setupRunReducer", () => {
  it("follows progress then the result", () => {
    const state = run([
      { kind: "started", action: "model.pull" },
      line({ type: "progress", current: 42, total: 100, message: "downloading" }),
    ]);
    expect(state).toEqual({
      status: "running",
      action: "model.pull",
      percent: 42,
      message: "downloading",
    });

    const done = setupRunReducer(
      state,
      line({ type: "result", summary: "Modèle téléchargé.", outputs: [] }),
    );
    expect(done).toEqual({ status: "done", action: "model.pull", message: "Modèle téléchargé." });
  });

  it("keeps the engine error and ignores the exit that follows", () => {
    const state = run([
      { kind: "started", action: "oda.install" },
      line({ type: "error", message: "winget absent", file: null, hint: "Page" }),
      { kind: "exit", code: 1 },
    ]);

    expect(state).toEqual({
      status: "failed",
      action: "oda.install",
      error: { message: "winget absent", hint: "Page", file: null },
    });
  });

  it("reports a silent crash", () => {
    const state = run([
      { kind: "started", action: "ollama.start" },
      { kind: "exit", code: 2 },
    ]);

    expect(state.status).toBe("failed");
  });
});

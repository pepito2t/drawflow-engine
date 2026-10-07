import { describe, expect, it } from "vitest";
import { BEHAVIORS } from "./behaviors";
import { FakeSocket } from "./fake-socket.test-helper";
import { DrawflowHub } from "./hub";

function readyHub(language: "fr" | "en" = "fr"): { hub: DrawflowHub; socket: FakeSocket } {
  const socket = new FakeSocket();
  const hub = new DrawflowHub(() => socket, { language });
  hub.configure(51717, "secret");
  socket.open();
  socket.receive({ type: "welcome", version: 1, locked: false });
  return { hub, socket };
}

const runEvent = (event: object): object => ({ type: "event", event });

describe("cancel-all key", () => {
  it("turns orange with the number of runs while something is running", () => {
    const { hub, socket } = readyHub();
    const behavior = BEHAVIORS["ch.drawflow.cancel-all"];
    socket.receive(runEvent({ type: "runStarted", moduleId: "a" }));
    socket.receive(runEvent({ type: "runStarted", moduleId: "b" }));

    expect(behavior?.face(hub, {})).toMatchObject({ tone: "warning", detail: "2 en cours" });

    socket.receive(runEvent({ type: "runFinished", moduleId: "a", outcome: "cancelled" }));
    socket.receive(runEvent({ type: "runFinished", moduleId: "b", outcome: "cancelled" }));
    expect(behavior?.face(hub, {})).toMatchObject({ tone: "idle", detail: null });
  });
});

describe("key texts", () => {
  it("are in English when Stream Dock runs in English", async () => {
    const { hub } = readyHub("en");

    expect(BEHAVIORS["ch.drawflow.preset"]?.face(hub, {}).label).toBe("Choose a preset");
    await expect(BEHAVIORS["ch.drawflow.open-tab"]?.press(hub, {})).resolves.toEqual({
      failed: "Choose a tab in the key settings",
    });
  });
});

describe("command key", () => {
  const behavior = BEHAVIORS["ch.drawflow.command"];

  it("shows the label of the chosen command in the language of Stream Dock", () => {
    const { hub } = readyHub("en");

    expect(behavior?.face(hub, { commandId: "mail.fetch" })).toMatchObject({
      tone: "idle",
      label: "Fetch mail",
    });
    expect(behavior?.face(hub, {}).label).toBe("Choose a command");
    expect(behavior?.face(hub, { commandId: "gone.command" }).label).toBe("Unknown command");
  });

  it("sends the chosen command without argument and reports the answer", async () => {
    const { hub, socket } = readyHub();

    const pressed = behavior?.press(hub, { commandId: "settings.open" });
    const request = socket.sent.at(-1) as { id: string; command: string; args: unknown };
    expect(request).toMatchObject({ command: "settings.open", args: {} });
    socket.receive({ type: "result", id: request.id, ok: false, error: "Fermée" });

    await expect(pressed).resolves.toEqual({ failed: "Fermée" });
  });

  it("refuses to send a command that is not chosen or no longer known", async () => {
    const { hub, socket } = readyHub();

    await expect(behavior?.press(hub, {})).resolves.toEqual({
      failed: "Choisissez une commande dans les réglages de la touche",
    });
    await expect(behavior?.press(hub, { commandId: "gone.command" })).resolves.toEqual({
      failed: expect.stringContaining("n'existe plus") as string,
    });
    const sentCommands = socket.sent.filter((message) => message.type === "command");
    expect(sentCommands.map((message) => message.command)).toEqual(["app.state"]);
  });
});

describe("runs-counter key", () => {
  it("reloads the state from Drawflow when pressed", async () => {
    const { hub, socket } = readyHub();
    const behavior = BEHAVIORS["ch.drawflow.runs-counter"];

    const pressed = behavior?.press(hub, {});
    const request = socket.sent.at(-1) as { id: string; command: string };
    expect(request.command).toBe("app.state");
    socket.receive({
      type: "result",
      id: request.id,
      ok: true,
      data: {
        modules: [{ id: "a", name: "Pièces", icon: "parts" }],
        presets: [],
        runs: [{ moduleId: "a", status: "running", current: 1, total: 4 }],
      },
    });

    await expect(pressed).resolves.toBe("ok");
    expect(hub.moduleName("a")).toBe("Pièces");
    expect(behavior?.face(hub, {})).toMatchObject({ tone: "running", detail: "1 en cours" });
  });

  it("warns when Drawflow cannot be read", async () => {
    const socket = new FakeSocket();
    const hub = new DrawflowHub(() => socket);

    await expect(BEHAVIORS["ch.drawflow.runs-counter"]?.press(hub, {})).resolves.toEqual({
      failed: expect.stringContaining("Drawflow") as string,
    });
  });
});

describe("preset key held down", () => {
  it("has nothing to do when its preset is not running", () => {
    const { hub } = readyHub();

    expect(BEHAVIORS["ch.drawflow.preset"]?.longPress?.(hub, { presetId: "p1" })).toBeNull();
    expect(BEHAVIORS["ch.drawflow.preset"]?.longPress?.(hub, {})).toBeNull();
  });
});

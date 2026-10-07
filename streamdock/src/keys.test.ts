import { describe, expect, it } from "vitest";
import { FakeSocket } from "./fake-socket.test-helper";
import { StreamDockHost, parseLaunchArguments } from "./host";
import { DrawflowHub } from "./hub";
import { KeyController, LONG_PRESS_MS } from "./keys";

const ARGV = ["-port", "1", "-pluginUUID", "plugin", "-registerEvent", "registerPlugin"];

interface Timer {
  callback: () => void;
  delayMs: number;
}

function setup(): { host: FakeSocket; drawflow: FakeSocket[]; timers: Timer[] } {
  const host = new FakeSocket();
  const drawflow: FakeSocket[] = [];
  const timers: Timer[] = [];
  const fakeTimers = {
    setTimer: (callback: () => void, delayMs: number): Timer => {
      const timer = { callback, delayMs };
      timers.push(timer);
      return timer;
    },
    clearTimer: (timer: unknown): void => {
      timers.splice(timers.indexOf(timer as Timer), 1);
    },
  };
  const hub = new DrawflowHub(() => {
    const socket = new FakeSocket();
    drawflow.push(socket);
    return socket;
  }, fakeTimers);
  new KeyController(new StreamDockHost(host, parseLaunchArguments(ARGV)), hub, fakeTimers);
  return { host, drawflow, timers };
}

const PRESET_KEY = { action: "ch.drawflow.preset", context: "k1" };
const RUNNING_STATE = {
  modules: [{ id: "a", name: "Pièces", icon: "parts" }],
  presets: [{ id: "p1", name: "Tour B", module: "a" }],
  runs: [{ moduleId: "a", status: "running", current: 1, total: 4 }],
};

const settle = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 0));

interface ReadyKey {
  host: FakeSocket;
  socket: FakeSocket;
  timers: Timer[];
}

/** A preset key whose run is going, Drawflow connected and its state loaded. */
async function runningPresetKey(): Promise<ReadyKey> {
  const { host, drawflow, timers } = setup();
  host.receive({
    event: "didReceiveGlobalSettings",
    payload: { settings: { port: "51717", token: "secret" } },
  });
  const socket = drawflow[0];
  if (!socket) throw new Error("no Drawflow socket");
  socket.open();
  socket.receive({ type: "welcome", version: 1, locked: false });
  answerLast(socket, { ok: true, data: RUNNING_STATE });
  await settle();
  host.receive({ event: "willAppear", ...PRESET_KEY, payload: { settings: { presetId: "p1" } } });
  return { host, socket, timers };
}

function answerLast(socket: FakeSocket, answer: object): void {
  const request = socket.sent.at(-1) as { id: string };
  socket.receive({ type: "result", id: request.id, ...answer });
}

const commandsSent = (socket: FakeSocket): unknown[] =>
  socket.sent.filter((message) => message.type === "command").map((message) => message.command);

function fireLongPress(timers: Timer[]): void {
  const hold = timers.find((timer) => timer.delayMs === LONG_PRESS_MS);
  if (!hold) throw new Error("no long-press timer");
  hold.callback();
}

const lastImage = (host: FakeSocket): string => {
  const image = host.sent.findLast((message) => message.event === "setImage");
  return decodeURIComponent((image?.payload as { image: string }).image);
};

describe("KeyController", () => {
  it("draws a key as soon as it appears, offline while Drawflow is not configured", () => {
    const { host } = setup();

    host.receive({
      event: "willAppear",
      action: "ch.drawflow.preset",
      context: "k1",
      payload: { settings: {} },
    });

    const image = host.sent.find((message) => message.event === "setImage");
    expect(image).toMatchObject({ context: "k1" });
    expect(host.sentEvents()).not.toContain("setTitle");
    expect(decodeURIComponent((image?.payload as { image: string }).image)).toContain("Hors ligne");
  });

  it("draws the progress of a run on the key of its preset", async () => {
    const { host, drawflow } = setup();
    host.receive({
      event: "didReceiveGlobalSettings",
      payload: { settings: { port: "51717", token: "secret" } },
    });
    const socket = drawflow[0];
    if (!socket) throw new Error("no socket");
    socket.open();
    socket.receive({ type: "welcome", version: 1, locked: false });
    const request = socket.sent.at(-1) as { id: string };
    socket.receive({
      type: "result",
      id: request.id,
      ok: true,
      data: {
        modules: [{ id: "dwg-parts", name: "Pièces", icon: "parts" }],
        presets: [{ id: "p1", name: "Tour B", module: "dwg-parts" }],
        runs: [],
      },
    });
    await new Promise((resolve) => setImmediate(resolve));
    host.receive({ event: "willAppear", ...PRESET_KEY, payload: { settings: { presetId: "p1" } } });

    socket.receive({
      type: "event",
      event: { type: "runProgress", moduleId: "dwg-parts", current: 2, total: 4 },
    });

    expect(lastImage(host)).toContain("Tour B");
    expect(lastImage(host)).toContain("50 %");
    expect(lastImage(host)).toContain('width="56"');
  });

  it("stops drawing a key once it has disappeared", () => {
    const { host, drawflow } = setup();
    host.receive({ event: "willAppear", ...PRESET_KEY, payload: { settings: {} } });
    host.receive({
      event: "didReceiveGlobalSettings",
      payload: { settings: { port: "51717", token: "secret" } },
    });
    host.receive({ event: "willDisappear", ...PRESET_KEY });
    const drawn = host.sentEvents().filter((event) => event === "setImage").length;

    drawflow[0]?.open();
    drawflow[0]?.receive({ type: "welcome", version: 1, locked: false });

    expect(host.sentEvents().filter((event) => event === "setImage")).toHaveLength(drawn);
  });

  it("ignores keys of other plugins", () => {
    const { host } = setup();

    host.receive({ event: "willAppear", action: "com.other.key", context: "k2", payload: {} });

    expect(host.sentEvents()).not.toContain("setImage");
  });

  it("shows why a press failed on the key for three seconds", async () => {
    const { host, timers } = setup();
    host.receive({ event: "willAppear", ...PRESET_KEY, payload: { settings: {} } });

    host.receive({ event: "keyUp", ...PRESET_KEY });
    await Promise.resolve();

    expect(host.sentEvents()).toContain("showAlert");
    expect(lastImage(host)).toContain("Choisissez un");
    const notice = timers.find((timer) => timer.delayMs === 3_000);
    if (!notice) throw new Error("no notice timer");
    notice.callback();
    expect(lastImage(host)).not.toContain("Choisissez un");
    expect(lastImage(host)).toContain("Hors ligne");
  });

  it("forgets a pending notice when the key disappears", async () => {
    const { host, timers } = setup();
    host.receive({ event: "willAppear", ...PRESET_KEY, payload: { settings: {} } });
    host.receive({ event: "keyUp", ...PRESET_KEY });
    await Promise.resolve();

    host.receive({ event: "willDisappear", ...PRESET_KEY });

    expect(timers.filter((timer) => timer.delayMs === 3_000)).toHaveLength(0);
  });

  it("connects to Drawflow with the port and token from the global settings", () => {
    const { host, drawflow } = setup();

    host.receive({
      event: "didReceiveGlobalSettings",
      payload: { settings: { port: "51800", token: "secret" } },
    });

    expect(drawflow).toHaveLength(1);
  });

  it("answers the settings panel with Drawflow's features", () => {
    const { host } = setup();

    host.receive({
      event: "sendToPlugin",
      action: "ch.drawflow.open-tab",
      context: "k3",
      payload: { event: "getModules" },
    });

    expect(host.sent.at(-1)).toEqual({
      event: "sendToPropertyInspector",
      action: "ch.drawflow.open-tab",
      context: "k3",
      payload: { event: "getModules", items: [], connection: "offline" },
    });
  });

  it("answers the settings panel with the commands it can send, even offline", () => {
    const { host } = setup();

    host.receive({
      event: "sendToPlugin",
      action: "ch.drawflow.command",
      context: "k4",
      payload: { event: "getCommands" },
    });

    const answer = host.sent.at(-1) as { payload: { items: { label: string; value: string }[] } };
    expect(answer.payload.items).toContainEqual({ label: "Paramètres", value: "settings.open" });
    expect(answer.payload.items).toContainEqual({
      label: "Relever les courriels",
      value: "mail.fetch",
    });
  });

  it("cancels the run of a preset key held down, then ignores its release", async () => {
    const { host, socket, timers } = await runningPresetKey();

    host.receive({ event: "keyDown", ...PRESET_KEY });
    fireLongPress(timers);

    expect(socket.sent.at(-1)).toMatchObject({ command: "runs.cancel", args: { moduleId: "a" } });
    expect(lastImage(host)).toContain("Annulation…");
    answerLast(socket, { ok: true });
    host.receive({ event: "keyUp", ...PRESET_KEY });
    await settle();

    expect(commandsSent(socket)).toEqual(["app.state", "runs.cancel"]);
    expect(lastImage(host)).toContain("Annulation…");
  });

  it("presses the key normally when it is released before the long press", async () => {
    const { host, socket, timers } = await runningPresetKey();

    host.receive({ event: "keyDown", ...PRESET_KEY });
    host.receive({ event: "keyUp", ...PRESET_KEY });
    await settle();

    expect(timers.filter((timer) => timer.delayMs === LONG_PRESS_MS)).toHaveLength(0);
    expect(commandsSent(socket)).toEqual(["app.state", "preset.run"]);
  });

  it("presses a held key normally on release when nothing is running", async () => {
    const { host, socket, timers } = await runningPresetKey();
    socket.receive({
      type: "event",
      event: { type: "runFinished", moduleId: "a", outcome: "succeeded" },
    });

    host.receive({ event: "keyDown", ...PRESET_KEY });
    fireLongPress(timers);
    host.receive({ event: "keyUp", ...PRESET_KEY });
    await settle();

    expect(commandsSent(socket)).toEqual(["app.state", "preset.run"]);
  });

  it("shows why a cancellation was refused and the run again", async () => {
    const { host, socket, timers } = await runningPresetKey();

    host.receive({ event: "keyDown", ...PRESET_KEY });
    fireLongPress(timers);
    answerLast(socket, { ok: false, error: "Refusé" });
    await settle();

    expect(host.sentEvents()).toContain("showAlert");
    expect(lastImage(host)).toContain("Refusé");
    timers.find((timer) => timer.delayMs === 3_000)?.callback();
    expect(lastImage(host)).toContain("25 %");
  });
});

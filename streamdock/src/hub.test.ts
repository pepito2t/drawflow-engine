import { describe, expect, it } from "vitest";
import { FakeSocket } from "./fake-socket.test-helper";
import { DrawflowHub } from "./hub";

interface Timer {
  callback: () => void;
  delayMs: number;
}

function setup(): { hub: DrawflowHub; urls: string[]; sockets: FakeSocket[]; timers: Timer[] } {
  const urls: string[] = [];
  const sockets: FakeSocket[] = [];
  const timers: Timer[] = [];
  const hub = new DrawflowHub(
    (url) => {
      urls.push(url);
      const socket = new FakeSocket();
      sockets.push(socket);
      return socket;
    },
    {
      setTimer: (callback, delayMs) => {
        const timer = { callback, delayMs };
        timers.push(timer);
        return timer;
      },
      clearTimer: (timer) => {
        timers.splice(timers.indexOf(timer as Timer), 1);
      },
    },
  );
  return { hub, urls, sockets, timers };
}

function readyHub() {
  const context = setup();
  context.hub.configure(51717, "secret");
  const socket = context.sockets[0];
  if (!socket) throw new Error("no socket");
  socket.open();
  socket.receive({ type: "welcome", version: 1, locked: false });
  return { ...context, socket };
}

const RUNNING_STATE = {
  modules: [],
  presets: [],
  runs: [{ moduleId: "a", status: "running", current: null, total: null }],
};
const IDLE_STATE = { modules: [], presets: [], runs: [] };

function answerLastCommand(socket: FakeSocket, data: unknown): void {
  const request = socket.sent.at(-1) as { id: string };
  socket.receive({ type: "result", id: request.id, ok: true, data });
}

const RESYNC_MS = 30_000;
const resyncTimers = (timers: Timer[]): Timer[] =>
  timers.filter((timer) => timer.delayMs === RESYNC_MS);

function fire(timers: Timer[], timer: Timer): void {
  timers.splice(timers.indexOf(timer), 1);
  timer.callback();
}

const commandsSent = (socket: FakeSocket): unknown[] =>
  socket.sent.filter((message) => message.type === "command").map((message) => message.command);

describe("DrawflowHub connection settings", () => {
  it("prefers Drawflow's own settings over what was typed in a key", () => {
    const { hub, urls } = setup();

    hub.setAutomatic({ port: 51717, token: "auto" });
    hub.configure(60000, "typed");

    expect(urls).toEqual(["ws://127.0.0.1:51717"]);
  });

  it("falls back to the key settings when Drawflow's file disappears", () => {
    const { hub, urls } = setup();

    hub.configure(60000, "typed");
    hub.setAutomatic({ port: 51717, token: "auto" });
    hub.setAutomatic(null);

    expect(urls).toEqual(["ws://127.0.0.1:60000", "ws://127.0.0.1:51717", "ws://127.0.0.1:60000"]);
  });

  it("stays offline without any settings", () => {
    const { hub, urls } = setup();

    hub.setAutomatic(null);
    hub.configure(60000, "");

    expect(urls).toEqual([]);
    expect(hub.connection).toBe("offline");
  });
});

describe("DrawflowHub resynchronisation", () => {
  it("reloads the state when Drawflow asks for a resync", () => {
    const { socket } = readyHub();
    answerLastCommand(socket, IDLE_STATE);

    socket.receive({ type: "event", event: { type: "resync" } });

    expect(commandsSent(socket)).toEqual(["app.state", "app.state"]);
  });

  it("reloads the state every 30 s while a run is going, then stops", async () => {
    const { hub, socket, timers } = readyHub();
    answerLastCommand(socket, IDLE_STATE);
    await Promise.resolve();
    expect(resyncTimers(timers)).toHaveLength(0);

    socket.receive({ type: "event", event: { type: "runStarted", moduleId: "a" } });
    const first = resyncTimers(timers)[0];
    if (!first) throw new Error("no periodic reload");

    fire(timers, first);
    expect(commandsSent(socket)).toEqual(["app.state", "app.state"]);
    answerLastCommand(socket, RUNNING_STATE);
    await Promise.resolve();
    const second = resyncTimers(timers)[0];
    if (!second) throw new Error("no periodic reload while still running");

    fire(timers, second);
    answerLastCommand(socket, IDLE_STATE);
    await Promise.resolve();
    expect(hub.runs.size).toBe(0);
    expect(resyncTimers(timers)).toHaveLength(0);
  });

  it("drops the periodic reload when Drawflow goes offline", () => {
    const { socket, timers } = readyHub();
    socket.receive({ type: "event", event: { type: "runStarted", moduleId: "a" } });
    expect(resyncTimers(timers)).toHaveLength(1);

    socket.remoteClose();

    expect(resyncTimers(timers)).toHaveLength(0);
  });
});

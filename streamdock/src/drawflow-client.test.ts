import { describe, expect, it } from "vitest";
import { DrawflowClient } from "./drawflow-client";
import { FakeSocket } from "./fake-socket.test-helper";

interface Timer {
  callback: () => void;
  delayMs: number;
}

function setup() {
  const sockets: FakeSocket[] = [];
  const timers: Timer[] = [];
  const client = new DrawflowClient({
    createSocket: () => {
      const socket = new FakeSocket();
      sockets.push(socket);
      return socket;
    },
    setTimer: (callback, delayMs) => {
      const timer = { callback, delayMs };
      timers.push(timer);
      return timer;
    },
    clearTimer: (timer) => {
      timers.splice(timers.indexOf(timer as Timer), 1);
    },
  });
  return { client, sockets, timers };
}

function fire(timers: Timer[], timer: Timer | undefined): void {
  if (!timer) throw new Error("no timer to fire");
  timers.splice(timers.indexOf(timer), 1);
  timer.callback();
}

function readyClient() {
  const context = setup();
  context.client.configure({ port: 51717, token: "secret" });
  const socket = context.sockets[0];
  if (!socket) throw new Error("no socket");
  socket.open();
  socket.receive({ type: "welcome", version: 1, locked: false });
  return { ...context, socket };
}

describe("DrawflowClient", () => {
  it("says hello with the token and becomes ready", () => {
    const { client, socket } = readyClient();

    expect(socket.sent[0]).toEqual({ type: "hello", token: "secret", version: 1 });
    expect(client.state).toBe("ready");
  });

  it("does not connect without a token", () => {
    const { client, sockets } = setup();

    client.configure({ port: 51717, token: "" });

    expect(sockets).toHaveLength(0);
  });

  it("resolves commands with the matching reply", async () => {
    const { client, socket } = readyClient();

    const pending = client.command("tab.open", { moduleId: "dwg-parts" });
    expect(socket.sent[1]).toEqual({
      type: "command",
      id: "1",
      command: "tab.open",
      args: { moduleId: "dwg-parts" },
    });
    socket.receive({ type: "result", id: "1", ok: true });

    await expect(pending).resolves.toEqual({ ok: true, data: undefined });
  });

  it("refuses commands while locked", async () => {
    const { client, socket } = readyClient();
    socket.receive({ type: "locked", locked: true });

    const result = await client.command("preset.run", { presetId: "a" });

    expect(client.state).toBe("locked");
    expect(result).toMatchObject({ ok: false });
  });

  it("forwards events to listeners", () => {
    const { client, socket } = readyClient();
    const events: unknown[] = [];
    client.onEvent((event) => events.push(event));

    socket.receive({ type: "event", event: { type: "runStarted", moduleId: "a" } });

    expect(events).toEqual([{ type: "runStarted", moduleId: "a" }]);
  });

  it("goes offline, fails pending commands and reconnects", async () => {
    const { client, socket, sockets, timers } = readyClient();
    const pending = client.command("app.state");

    socket.remoteClose();

    expect(client.state).toBe("offline");
    await expect(pending).resolves.toMatchObject({ ok: false });
    fire(timers, timers.at(-1));
    expect(sockets).toHaveLength(2);
  });

  it("waits 2, 4, 8 then 15 s between attempts, and starts over once welcomed", () => {
    const { client, sockets, timers } = readyClient();
    const delays: number[] = [];

    for (let attempt = 0; attempt < 5; attempt++) {
      sockets.at(-1)?.remoteClose();
      const reconnect = timers.at(-1);
      delays.push(reconnect?.delayMs ?? -1);
      fire(timers, reconnect);
    }
    expect(delays).toEqual([2_000, 4_000, 8_000, 15_000, 15_000]);

    sockets.at(-1)?.open();
    sockets.at(-1)?.receive({ type: "welcome", version: 1, locked: false });
    sockets.at(-1)?.remoteClose();
    expect(timers.at(-1)?.delayMs).toBe(2_000);
    expect(client.state).toBe("offline");
  });

  it("keeps a single socket when reconfigured, even if the old one closes late", () => {
    const { client, sockets, timers } = readyClient();

    client.configure({ port: 51718, token: "secret" });
    expect(sockets).toHaveLength(2);
    expect(sockets[0]?.closed).toBe(true);

    sockets[0]?.remoteClose();
    expect(timers).toHaveLength(0);
    expect(sockets).toHaveLength(2);
  });

  it("gives up on a command after 20 s without answer", async () => {
    const { client, timers } = readyClient();

    const pending = client.command("app.state");
    const timeout = timers.at(-1);
    expect(timeout?.delayMs).toBe(20_000);
    fire(timers, timeout);

    await expect(pending).resolves.toEqual({
      ok: false,
      error: "Drawflow n'a pas répondu à temps.",
    });
  });

  it("marks the token as refused when Drawflow answers with an error instead of welcome", async () => {
    const { client, sockets, timers } = setup();
    client.configure({ port: 51717, token: "wrong" });
    const socket = sockets[0];
    socket?.open();

    socket?.receive({ type: "error", message: "Jeton ou version de protocole invalide." });
    socket?.remoteClose();

    expect(client.state).toBe("refused");
    expect(socket?.closed).toBe(true);
    expect(timers).toHaveLength(0);
    await expect(client.command("app.state")).resolves.toMatchObject({
      ok: false,
      error: expect.stringContaining("Jeton") as string,
    });
  });

  it("tries again only once the settings change after a refusal", () => {
    const { client, sockets } = setup();
    client.configure({ port: 51717, token: "wrong" });
    sockets[0]?.open();
    sockets[0]?.receive({ type: "error", message: "Jeton ou version de protocole invalide." });

    client.configure({ port: 51717, token: "wrong" });
    expect(sockets).toHaveLength(1);

    client.configure({ port: 51717, token: "right" });
    expect(sockets).toHaveLength(2);
    expect(client.state).toBe("offline");
  });

  it("ignores malformed server messages", () => {
    const { client, socket } = readyClient();

    socket.receive({ type: "surprise" });

    expect(client.state).toBe("ready");
  });
});

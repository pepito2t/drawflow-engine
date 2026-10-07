import { describe, expect, it } from "vitest";
import { DrawflowClient } from "./drawflow-client";
import { FakeSocket } from "./fake-socket.test-helper";

function setup() {
  const sockets: FakeSocket[] = [];
  const timers: (() => void)[] = [];
  const client = new DrawflowClient({
    createSocket: () => {
      const socket = new FakeSocket();
      sockets.push(socket);
      return socket;
    },
    setTimer: (callback) => {
      timers.push(callback);
      return timers.length;
    },
    clearTimer: () => undefined,
  });
  return { client, sockets, timers };
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
    const reconnect = timers.at(-1);
    reconnect?.();
    expect(sockets).toHaveLength(2);
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

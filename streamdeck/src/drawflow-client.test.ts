import { describe, expect, it } from "vitest";
import { DrawflowClient, type SocketLike } from "./drawflow-client";

class FakeSocket implements SocketLike {
  sent: unknown[] = [];
  closed = false;
  private open: () => void = () => undefined;
  private message: (data: string) => void = () => undefined;
  private close_: () => void = () => undefined;

  send(data: string): void {
    this.sent.push(JSON.parse(data));
  }
  close(): void {
    this.closed = true;
    this.close_();
  }
  onOpen(listener: () => void): void {
    this.open = listener;
  }
  onMessage(listener: (data: string) => void): void {
    this.message = listener;
  }
  onClose(listener: () => void): void {
    this.close_ = listener;
  }
  serverOpens(): void {
    this.open();
  }
  serverSays(message: object): void {
    this.message(JSON.stringify(message));
  }
  serverCloses(): void {
    this.close_();
  }
}

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
  socket.serverOpens();
  socket.serverSays({ type: "welcome", version: 1, locked: false });
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
    socket.serverSays({ type: "result", id: "1", ok: true });

    await expect(pending).resolves.toEqual({ ok: true, data: undefined });
  });

  it("refuses commands while locked", async () => {
    const { client, socket } = readyClient();
    socket.serverSays({ type: "locked", locked: true });

    const result = await client.command("preset.run", { presetId: "a" });

    expect(client.state).toBe("locked");
    expect(result).toMatchObject({ ok: false });
  });

  it("forwards events to listeners", () => {
    const { client, socket } = readyClient();
    const events: unknown[] = [];
    client.onEvent((event) => events.push(event));

    socket.serverSays({ type: "event", event: { type: "runStarted", moduleId: "a" } });

    expect(events).toEqual([{ type: "runStarted", moduleId: "a" }]);
  });

  it("goes offline, fails pending commands and reconnects", async () => {
    const { client, socket, sockets, timers } = readyClient();
    const pending = client.command("app.state");

    socket.serverCloses();

    expect(client.state).toBe("offline");
    await expect(pending).resolves.toMatchObject({ ok: false });
    const reconnect = timers.at(-1);
    reconnect?.();
    expect(sockets).toHaveLength(2);
  });

  it("ignores malformed server messages", () => {
    const { client, socket } = readyClient();

    socket.serverSays({ type: "surprise" });

    expect(client.state).toBe("ready");
  });
});

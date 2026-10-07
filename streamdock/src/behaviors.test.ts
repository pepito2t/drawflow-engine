import { describe, expect, it } from "vitest";
import { BEHAVIORS } from "./behaviors";
import { FakeSocket } from "./fake-socket.test-helper";
import { DrawflowHub } from "./hub";

function readyHub(): { hub: DrawflowHub; socket: FakeSocket } {
  const socket = new FakeSocket();
  const hub = new DrawflowHub(() => socket);
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

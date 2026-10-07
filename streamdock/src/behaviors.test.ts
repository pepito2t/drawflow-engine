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

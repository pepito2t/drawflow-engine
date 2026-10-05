import { describe, expect, it } from "vitest";
import { FakeSocket } from "./fake-socket.test-helper";
import { StreamDockHost, parseLaunchArguments } from "./host";
import { DrawflowHub } from "./hub";
import { KeyController } from "./keys";

const ARGV = ["-port", "1", "-pluginUUID", "plugin", "-registerEvent", "registerPlugin"];

function setup(): { host: FakeSocket; drawflow: FakeSocket[] } {
  const host = new FakeSocket();
  const drawflow: FakeSocket[] = [];
  const hub = new DrawflowHub(() => {
    const socket = new FakeSocket();
    drawflow.push(socket);
    return socket;
  });
  new KeyController(new StreamDockHost(host, parseLaunchArguments(ARGV)), hub);
  return { host, drawflow };
}

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
    expect(decodeURIComponent((image?.payload as { image: string }).image)).toContain("Hors ligne");
  });

  it("ignores keys of other plugins", () => {
    const { host } = setup();

    host.receive({ event: "willAppear", action: "com.other.key", context: "k2", payload: {} });

    expect(host.sentEvents()).not.toContain("setImage");
  });

  it("warns on the key when a preset key has no preset", async () => {
    const { host } = setup();
    host.receive({
      event: "willAppear",
      action: "ch.drawflow.preset",
      context: "k1",
      payload: { settings: {} },
    });

    host.receive({ event: "keyUp", action: "ch.drawflow.preset", context: "k1" });
    await Promise.resolve();

    expect(host.sent.at(-1)).toEqual({ event: "showAlert", context: "k1" });
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
      payload: { event: "getModules", items: [] },
    });
  });
});

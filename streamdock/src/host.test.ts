import { describe, expect, it } from "vitest";
import { FakeSocket } from "./fake-socket.test-helper";
import { LaunchError, StreamDockHost, parseHostEvent, parseLaunchArguments } from "./host";

const ARGV = [
  "node",
  "plugin.js",
  "-port",
  "23519",
  "-pluginUUID",
  "abc123",
  "-registerEvent",
  "registerPlugin",
  "-info",
  '{"application":{"language":"fr"}}',
];

describe("parseLaunchArguments", () => {
  it("reads the arguments Stream Dock passes to the plugin", () => {
    expect(parseLaunchArguments(ARGV)).toEqual({
      port: 23519,
      pluginUUID: "abc123",
      registerEvent: "registerPlugin",
    });
  });

  it("refuses to start outside Stream Dock", () => {
    expect(() => parseLaunchArguments(["node", "plugin.js"])).toThrow(LaunchError);
  });
});

describe("StreamDockHost", () => {
  it("registers then asks for the global settings once connected", () => {
    const socket = new FakeSocket();
    new StreamDockHost(socket, parseLaunchArguments(ARGV));

    socket.open();

    expect(socket.sent).toEqual([
      { event: "registerPlugin", uuid: "abc123" },
      { event: "getGlobalSettings", context: "abc123" },
    ]);
  });

  it("ignores messages it cannot read", () => {
    expect(parseHostEvent("pas du json")).toBeNull();
    expect(parseHostEvent('{"no":"event"}')).toBeNull();
    expect(parseHostEvent('{"event":"keyUp","context":"k1"}')).toEqual({
      event: "keyUp",
      context: "k1",
    });
  });
});

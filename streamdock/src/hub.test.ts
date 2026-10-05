import { describe, expect, it } from "vitest";
import { FakeSocket } from "./fake-socket.test-helper";
import { DrawflowHub } from "./hub";

function setup(): { hub: DrawflowHub; urls: string[] } {
  const urls: string[] = [];
  const hub = new DrawflowHub((url) => {
    urls.push(url);
    return new FakeSocket();
  });
  return { hub, urls };
}

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

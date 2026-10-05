import { describe, expect, it } from "vitest";
import { drawflowConfigPath, loadDrawflowConnection, parseDrawflowConfig } from "./drawflow-config";

const ENV = { APPDATA: "C:\\Users\\dessin\\AppData\\Roaming" };
const ENABLED = '{"enabled":true,"port":51717,"token":"secret"}';

describe("drawflow-config", () => {
  it("finds Drawflow's integrations file under APPDATA", () => {
    expect(drawflowConfigPath(ENV, "\\")).toBe(
      "C:\\Users\\dessin\\AppData\\Roaming\\ch.drawflow.desktop\\integrations.json",
    );
    expect(drawflowConfigPath({}, "\\")).toBeNull();
  });

  it("uses the file only when the local API is enabled with a token", () => {
    expect(parseDrawflowConfig(ENABLED)).toEqual({ port: 51717, token: "secret" });
    expect(parseDrawflowConfig('{"enabled":false,"port":51717,"token":"secret"}')).toBeNull();
    expect(parseDrawflowConfig('{"enabled":true,"port":51717,"token":""}')).toBeNull();
    expect(parseDrawflowConfig("pas du json")).toBeNull();
    expect(parseDrawflowConfig('{"port":"51717"}')).toBeNull();
  });

  it("reads the file at its path, or gives nothing when it is missing", () => {
    const files = new Map([[drawflowConfigPath(ENV, "\\") ?? "", ENABLED]]);
    const readFile = (path: string): string | null => files.get(path) ?? null;

    expect(loadDrawflowConnection(readFile, ENV, "\\")).toEqual({ port: 51717, token: "secret" });
    expect(loadDrawflowConnection(() => null, ENV, "\\")).toBeNull();
    expect(loadDrawflowConnection(readFile, {}, "\\")).toBeNull();
  });
});

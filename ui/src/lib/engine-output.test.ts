import { describe, expect, it } from "vitest";
import { EngineCommandError, unwrapEngineOutput } from "./engine-output";

describe("unwrapEngineOutput", () => {
  it("returns stdout on success", () => {
    expect(unwrapEngineOutput({ success: true, stdout: "[]\n" })).toBe("[]\n");
  });

  it("turns the engine error event into a typed error", () => {
    const stdout =
      '{"type":"error","message":"Fichier illisible","file":"s.json","hint":"Supprimez-le"}\n';

    expect(() => unwrapEngineOutput({ success: false, stdout })).toThrow(
      new EngineCommandError("Fichier illisible", "Supprimez-le", "s.json"),
    );
  });

  it("falls back to a generic error when stdout has no error event", () => {
    expect(() => unwrapEngineOutput({ success: false, stdout: "" })).toThrow(EngineCommandError);
  });

  it("rejects malformed bridge payloads", () => {
    expect(() => unwrapEngineOutput("oops")).toThrow();
  });
});

import { describe, expect, it } from "vitest";
import { isCommandId, parseCommandArguments } from "./commands";

describe("commands", () => {
  it("recognizes declared commands only", () => {
    expect(isCommandId("tab.open")).toBe(true);
    expect(isCommandId("system.shutdown")).toBe(false);
  });

  it("validates arguments", () => {
    expect(parseCommandArguments("tab.open", { moduleId: "dwg-parts" })).toEqual({
      ok: true,
      id: "tab.open",
      args: { moduleId: "dwg-parts" },
    });
    expect(parseCommandArguments("tab.open", {})).toEqual({
      ok: false,
      error: "Arguments invalides pour tab.open.",
    });
  });

  it("accepts missing arguments for argument-less commands", () => {
    expect(parseCommandArguments("runs.cancel-all", undefined)).toMatchObject({ ok: true });
  });

  it("rejects unknown commands", () => {
    expect(parseCommandArguments("nope", {})).toEqual({
      ok: false,
      error: "Commande inconnue : nope",
    });
  });
});

import { afterEach, describe, expect, it } from "vitest";
import errorSource from "../../../../src-tauri/src/error.rs?raw";
import integrationsSource from "../../../../src-tauri/src/integrations/mod.rs?raw";
import serverSource from "../../../../src-tauri/src/integrations/server.rs?raw";
import { setLanguage } from "../../i18n";
import { t } from "../../i18n/shell";
import { describeBridgeError } from "./engine";

const VARIANT_CODE = /=> "([a-z][A-Za-z]+)",/g;
const PROTOCOL_CODE = /_CODE: &str = "([a-z][A-Za-z]+)";/g;

function codesIn(source: string, pattern: RegExp): string[] {
  return [...source.matchAll(pattern)].flatMap((match) => match[1] ?? []);
}

describe("bridge error codes", () => {
  it("has a translation for every code Rust can send", () => {
    const codes = [
      ...codesIn(errorSource, VARIANT_CODE),
      ...codesIn(serverSource, PROTOCOL_CODE),
      ...codesIn(integrationsSource, PROTOCOL_CODE),
    ];
    expect(codes.length).toBeGreaterThan(30);
    expect(codes).toContain("noReply");
    for (const code of codes) {
      expect(t.has(`bridge.${code}`), `bridge.${code} absent de ui/src/i18n/shell.ts`).toBe(true);
    }
  });
});

describe("describeBridgeError", () => {
  afterEach(() => {
    setLanguage("fr");
  });

  it("translates the code with its parameters", () => {
    const error = { code: "engineTimeout", params: { seconds: 30 }, message: "English" };

    expect(describeBridgeError(error)).toBe(
      "Le moteur n'a pas répondu dans le délai imparti (30 s) ; il a été arrêté. Réessayez avec moins de fichiers à la fois.",
    );
    setLanguage("en");
    expect(describeBridgeError(error)).toBe(
      "The engine did not answer within 30 s; it was stopped. Try again with fewer files at once.",
    );
  });

  it("fills several parameters", () => {
    const error = {
      code: "invalidPort",
      params: { port: 80, min: 1024, max: 65535 },
      message: "Port 80 cannot be used",
    };

    expect(describeBridgeError(error)).toBe(
      "Le port 80 n'est pas utilisable : choisissez un port entre 1024 et 65535.",
    );
  });

  it("falls back to the message for a code it does not know", () => {
    const error = { code: "brandNew", params: {}, message: "Something new happened." };

    expect(describeBridgeError(error)).toBe("Something new happened.");
  });

  it("falls back to a generic text without code nor message", () => {
    expect(describeBridgeError({ code: "brandNew", params: {}, message: "" })).toBe(
      "Erreur de communication avec le moteur.",
    );
    expect(describeBridgeError(42)).toBe("Erreur de communication avec le moteur.");
  });

  it("ignores unusable parameters but keeps the translation", () => {
    const error = { code: "wrongAccessCode", params: null, message: "Wrong access code." };

    expect(describeBridgeError(error)).toBe("Code d'accès incorrect.");
  });

  it("shows plain string errors from Tauri plugins as they are", () => {
    expect(describeBridgeError("dialog closed unexpectedly")).toBe("dialog closed unexpectedly");
  });
});

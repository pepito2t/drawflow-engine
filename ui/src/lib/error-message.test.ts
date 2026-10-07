import { describe, expect, it } from "vitest";
import { CatalogError } from "./catalog";
import { EngineCommandError } from "./engine-output";
import { toReadableError } from "./error-message";

describe("toReadableError", () => {
  it("keeps bridge error strings as the message", () => {
    expect(toReadableError("Impossible de lancer le moteur").message).toBe(
      "Impossible de lancer le moteur",
    );
  });

  it("translates coded bridge errors", () => {
    const readable = toReadableError({
      code: "configCorrupted",
      params: { file: "automations.json" },
      message: "The file automations.json is unreadable.",
    });

    expect(readable).toEqual({
      message:
        "Le fichier automations.json est illisible : corrigez-le ou supprimez-le dans le dossier de configuration.",
      hint: null,
      file: null,
    });
  });

  it("suggests updating when the catalog is incompatible", () => {
    const readable = toReadableError(new CatalogError("Formulaire invalide"));

    expect(readable).toEqual({
      message: "Formulaire invalide",
      hint: "Mettez l'application à jour puis réessayez.",
      file: null,
    });
  });

  it("falls back to a generic message for unknown values", () => {
    expect(toReadableError(42).message).toBe("Une erreur inattendue est survenue.");
  });

  it("keeps the engine hint and file", () => {
    const readable = toReadableError(new EngineCommandError("Illisible", "Supprimez", "s.json"));

    expect(readable).toEqual({ message: "Illisible", hint: "Supprimez", file: "s.json" });
  });
});

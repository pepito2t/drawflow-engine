import { describe, expect, it } from "vitest";
import { CatalogError } from "./catalog";
import { toReadableError } from "./error-message";

describe("toReadableError", () => {
  it("keeps bridge error strings as the message", () => {
    expect(toReadableError("Impossible de lancer le moteur").message).toBe(
      "Impossible de lancer le moteur",
    );
  });

  it("suggests updating when the catalog is incompatible", () => {
    const readable = toReadableError(new CatalogError("Formulaire invalide"));

    expect(readable).toEqual({
      message: "Formulaire invalide",
      hint: "Mettez l'application à jour puis réessayez.",
    });
  });

  it("falls back to a generic message for unknown values", () => {
    expect(toReadableError(42).message).toBe("Une erreur inattendue est survenue.");
  });
});

import { afterEach, describe, expect, it } from "vitest";
import { currentLanguage, defineMessages, detectLanguage, plural, setLanguage } from "./index";

const t = defineMessages({
  fr: { hello: "Bonjour {name}", files: "fichiers" },
  en: { hello: "Hello {name}", files: "files" },
});

describe("i18n", () => {
  afterEach(() => {
    setLanguage("fr");
  });

  it("resolves the current language at call time with placeholders", () => {
    expect(t("hello", { name: "Léa" })).toBe("Bonjour Léa");
    setLanguage("en");
    expect(currentLanguage()).toBe("en");
    expect(t("hello", { name: "Léa" })).toBe("Hello Léa");
    expect(t("files")).toBe("files");
  });

  it("keeps unknown placeholders and handles plurals", () => {
    expect(t("hello")).toBe("Bonjour {name}");
    expect(plural(1, "{count} fichier", "{count} fichiers")).toBe("1 fichier");
    expect(plural(3, "{count} fichier", "{count} fichiers")).toBe("3 fichiers");
  });

  it("tells which keys built at run time exist", () => {
    expect(t.has("hello")).toBe(true);
    expect(t.has("missing")).toBe(false);
    expect(t.has("toString")).toBe(false);
  });

  it("falls back to a language without browser storage", () => {
    expect(["fr", "en"]).toContain(detectLanguage());
  });
});

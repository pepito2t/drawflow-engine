import { describe, expect, it } from "vitest";
import { CatalogError, parseCatalog } from "./catalog";

const helloEntry = {
  manifest: {
    id: "hello",
    name: "Bonjour",
    description: "Exemple",
    version: "0.1.0",
    order: 0,
    instructions: ["Choisir un dossier."],
  },
  inputs_schema: { properties: { name: { title: "Nom", "x-ui": "text" } }, required: ["name"] },
};

describe("parseCatalog", () => {
  it("builds modules with their form fields", () => {
    const [module] = parseCatalog(JSON.stringify([helloEntry]));

    expect(module?.manifest.id).toBe("hello");
    expect(module?.fields.map((field) => field.name)).toEqual(["name"]);
  });

  it("rejects malformed JSON", () => {
    expect(() => parseCatalog("{")).toThrow(CatalogError);
  });

  it("names the module whose schema lacks a ui kind", () => {
    const broken = { ...helloEntry, inputs_schema: { properties: { name: { title: "Nom" } } } };

    expect(() => parseCatalog(JSON.stringify([broken]))).toThrow(/hello/);
  });
});

import { describe, expect, it } from "vitest";
import { CatalogError } from "./catalog";
import { parseTemplateLibrary, templatesOfKind } from "./templates";

const library = {
  templates: [
    { id: "liste.xlsx", kind: "xlsx" },
    { id: "rapport.docx", kind: "docx" },
  ],
  modules: [{ id: "dwg-parts", name: "Liste de pièces", kind: "xlsx", default: "liste.xlsx" }],
};

describe("templates", () => {
  it("filters templates by kind", () => {
    expect(templatesOfKind(parseTemplateLibrary(JSON.stringify(library)), "xlsx")).toEqual([
      "liste.xlsx",
    ]);
  });

  it("rejects malformed responses", () => {
    expect(() => parseTemplateLibrary('{"templates": 1}')).toThrow(CatalogError);
  });
});

import { describe, expect, it } from "vitest";
import { describeProfileChanges, parseProfilePreview } from "./profile";

const PREVIEW = {
  app_version: "0.17.0",
  exported_at: "2026-10-06T08:00:00+00:00",
  sections: [
    { id: "general", title: "Général" },
    { id: "dwg-parts", title: "Liste de pièces" },
  ],
  presets: ["Façade nord"],
  templates: ["Liste entreprise.xlsx"],
  replaced_presets: 2,
  replaced_templates: ["Liste entreprise.xlsx"],
};

describe("profile", () => {
  it("parses the preview and refuses other payloads", () => {
    expect(parseProfilePreview(JSON.stringify(PREVIEW)).presets).toEqual(["Façade nord"]);
    expect(() => parseProfilePreview("{}")).toThrow("invalide");
  });

  it("explains what the import replaces", () => {
    const lines = describeProfileChanges(parseProfilePreview(JSON.stringify(PREVIEW)));
    expect(lines[0]).toContain("Général, Liste de pièces");
    expect(lines[1]).toContain("2 préréglages actuels sont supprimés");
    expect(lines[2]).toContain("Liste entreprise.xlsx remplacés");
    expect(
      describeProfileChanges({ ...PREVIEW, replaced_presets: 0, replaced_templates: [] })[1],
    ).toBe("1 préréglages importés.");
  });
});

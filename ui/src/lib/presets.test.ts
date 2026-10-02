import { describe, expect, it } from "vitest";
import { CatalogError } from "./catalog";
import { describeFields } from "./form-schema";
import { parsePresets, presetFormValues, presetsFor, type Preset } from "./presets";

const fields = describeFields({
  properties: {
    folders: { title: "Dossiers", "x-ui": "folders" },
    project: { title: "Projet", "x-ui": "text", default: "" },
    recursive: { title: "Sous-dossiers", "x-ui": "bool", default: true },
  },
});

const preset = (name: string, module = "dwg-parts"): Preset => ({
  id: name,
  name,
  module,
  inputs: { folders: ["C:\\Plans"], project: "Tour B" },
});

describe("presets", () => {
  it("parses the engine response", () => {
    expect(parsePresets(JSON.stringify({ presets: [preset("A")] }))).toEqual([preset("A")]);
    expect(() => parsePresets("{}")).toThrow(CatalogError);
  });

  it("keeps the presets of one feature, sorted by name", () => {
    const all = [preset("Zinc"), preset("Alu"), preset("Rapport", "pdf-report")];

    expect(presetsFor(all, "dwg-parts").map((item) => item.name)).toEqual(["Alu", "Zinc"]);
  });

  it("fills missing fields with form defaults", () => {
    expect(presetFormValues(preset("A"), fields)).toEqual({
      folders: ["C:\\Plans"],
      project: "Tour B",
      recursive: true,
    });
  });
});

import { describe, expect, it } from "vitest";
import { inputsForNewFile, newAutomation, validateAutomations } from "./automations";
import type { FieldDescriptor } from "./form-schema";
import type { Preset } from "./presets";

function field(name: string, kind: FieldDescriptor["kind"]): FieldDescriptor {
  return {
    name,
    label: name,
    description: null,
    kind,
    required: true,
    options: [],
    defaultValue: kind === "files" || kind === "folders" ? [] : "",
    mappingLabels: null,
  };
}

const PRESET: Preset = { id: "p1", name: "Façade", module: "dwg-parts", inputs: {} };

describe("automations", () => {
  it("puts the new file into the first file input of the preset", () => {
    const fields = [field("output_folder", "output_folder"), field("files", "files")];
    const inputs = inputsForNewFile(fields, { output_folder: "C:\\Sortie" }, "C:\\Plans\\a.dwg");
    expect(inputs).toEqual({ output_folder: "C:\\Sortie", files: ["C:\\Plans\\a.dwg"] });
    expect(inputsForNewFile([field("report", "file")], {}, "C:\\r.pdf")).toEqual({
      report: "C:\\r.pdf",
    });
  });

  it("refuses features without a file input", () => {
    expect(() => inputsForNewFile([field("folder", "folder")], {}, "C:\\a.dwg")).toThrow(
      "ne prend pas de fichier",
    );
  });

  it("validates folders and presets", () => {
    const valid = { ...newAutomation(), folder: "C:\\Plans", presetId: "p1" };
    expect(validateAutomations([valid], [PRESET])).toBeNull();
    expect(validateAutomations([{ ...valid, folder: " " }], [PRESET])).toMatch("dossier");
    expect(validateAutomations([{ ...valid, presetId: "gone" }], [PRESET])).toMatch("préréglage");
    expect(newAutomation().id).toHaveLength(8);
  });
});

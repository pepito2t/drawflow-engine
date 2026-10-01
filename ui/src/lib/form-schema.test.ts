import { describe, expect, it } from "vitest";
import {
  describeFields,
  initialValues,
  mergeDroppedPaths,
  toEngineInputs,
  UI_KINDS,
  type InputsSchema,
} from "./form-schema";

const helloSchema: InputsSchema = {
  properties: {
    name: { title: "Nom", "x-ui": "text" },
    output_folder: { title: "Dossier de sortie", "x-ui": "output_folder" },
  },
  required: ["name", "output_folder"],
};

describe("describeFields", () => {
  it("maps properties to field descriptors", () => {
    const [name, output] = describeFields(helloSchema);

    expect(name).toMatchObject({ name: "name", label: "Nom", kind: "text", required: true });
    expect(output).toMatchObject({ kind: "output_folder", defaultValue: "" });
  });

  it.each(UI_KINDS)("supports the %s kind", (kind) => {
    const [field] = describeFields({ properties: { value: { "x-ui": kind } } });

    expect(field?.kind).toBe(kind);
    expect(field?.required).toBe(false);
  });

  it("uses empty lists for multi-path kinds and false for booleans", () => {
    const fields = describeFields({
      properties: { plans: { "x-ui": "files" }, recursive: { "x-ui": "bool" } },
    });

    expect(initialValues(fields)).toEqual({ plans: [], recursive: false });
  });

  it("resolves enum options from $defs references", () => {
    const [field] = describeFields({
      properties: { format: { "x-ui": "enum", $ref: "#/$defs/Format" } },
      $defs: { Format: { enum: ["xlsx", "csv"] } },
    });

    expect(field?.options).toEqual(["xlsx", "csv"]);
    expect(field?.defaultValue).toBe("xlsx");
  });

  it("keeps declared defaults", () => {
    const [field] = describeFields({ properties: { label: { "x-ui": "text", default: "Lot A" } } });

    expect(field?.defaultValue).toBe("Lot A");
  });
});

describe("toEngineInputs", () => {
  it("omits empty values so the engine reports missing required fields", () => {
    const fields = describeFields(helloSchema);

    expect(toEngineInputs(fields, { name: "Zoé", output_folder: "" })).toEqual({ name: "Zoé" });
  });
});

describe("mergeDroppedPaths", () => {
  it("replaces the value of single-path fields with the first dropped path", () => {
    expect(mergeDroppedPaths("file", "C:\\old.dwg", ["C:\\a.dwg", "C:\\b.dwg"])).toBe("C:\\a.dwg");
  });

  it("appends unique paths to multi-path fields", () => {
    expect(mergeDroppedPaths("files", ["a.dwg"], ["a.dwg", "b.dwg"])).toEqual(["a.dwg", "b.dwg"]);
  });

  it("keeps the current value when nothing is dropped", () => {
    expect(mergeDroppedPaths("folder", "D:\\plans", [])).toBe("D:\\plans");
  });
});

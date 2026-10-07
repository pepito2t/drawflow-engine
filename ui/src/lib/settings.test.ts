import { describe, expect, it } from "vitest";
import { CatalogError } from "./catalog";
import {
  editedSections,
  mergeReloadedSettings,
  parseSettings,
  readNotificationThreshold,
  toSettingsPayload,
  valuesBySection,
} from "./settings";

const response = {
  sections: [
    {
      id: "general",
      title: "Général",
      schema: {
        properties: {
          oda_converter_path: { title: "ODA File Converter", "x-ui": "file", default: null },
          batch_size: { title: "Fichiers traités en parallèle", "x-ui": "number", default: 4 },
        },
      },
      values: { oda_converter_path: null, batch_size: 8 },
      error: null,
    },
  ],
};

describe("parseSettings", () => {
  it("builds sections with form values converted for inputs", () => {
    const [general] = parseSettings(JSON.stringify(response));

    expect(general?.title).toBe("Général");
    expect(general?.values).toEqual({ oda_converter_path: "", batch_size: "8" });
  });

  it("keeps the section error reported by the engine", () => {
    const withError = { sections: [{ ...response.sections[0], error: "Valeur invalide" }] };

    expect(parseSettings(JSON.stringify(withError))[0]?.error).toBe("Valeur invalide");
  });

  it("rejects malformed responses", () => {
    expect(() => parseSettings('{"sections": "nope"}')).toThrow(CatalogError);
  });
});

describe("toSettingsPayload", () => {
  it("omits empty values so the engine applies its defaults", () => {
    const sections = parseSettings(JSON.stringify(response));
    const values = valuesBySection(sections);

    expect(toSettingsPayload(sections, values)).toEqual({ general: { batch_size: "8" } });
  });
});

const twoSections = {
  sections: [
    response.sections[0],
    {
      id: "assistant",
      title: "Assistant",
      schema: { properties: { model: { title: "Modèle", "x-ui": "text", default: "" } } },
      values: { model: "llama3" },
      error: null,
    },
  ],
};

describe("editedSections", () => {
  it("keeps only the sections whose values differ from the loaded ones", () => {
    const sections = parseSettings(JSON.stringify(twoSections));
    const values = {
      ...valuesBySection(sections),
      general: { oda_converter_path: "", batch_size: "2" },
    };

    expect(editedSections(sections, values).map((section) => section.id)).toEqual(["general"]);
    expect(editedSections(sections, valuesBySection(sections))).toEqual([]);
  });
});

describe("mergeReloadedSettings", () => {
  it("takes the reloaded values except for sections still edited", () => {
    const sections = parseSettings(JSON.stringify(twoSections));
    const values = {
      ...valuesBySection(sections),
      general: { oda_converter_path: "", batch_size: "2" },
    };
    const reloaded = structuredClone(twoSections);
    Object.assign(reloaded.sections[1]?.values ?? {}, { model: "mistral" });
    Object.assign(reloaded.sections[0]?.values ?? {}, { batch_size: 16 });

    const merged = mergeReloadedSettings(sections, values, parseSettings(JSON.stringify(reloaded)));

    expect(merged.assistant).toEqual({ model: "mistral" });
    expect(merged.general).toEqual({ oda_converter_path: "", batch_size: "2" });
  });
});

describe("readNotificationThreshold", () => {
  it("reads the general threshold", () => {
    const withThreshold = structuredClone(response);
    const general = withThreshold.sections[0];
    if (!general) throw new Error("fixture");
    Object.assign(general.schema.properties, {
      notification_threshold_seconds: { title: "Notifier après", "x-ui": "number" },
    });
    Object.assign(general.values, { notification_threshold_seconds: 30 });

    expect(readNotificationThreshold(JSON.stringify(withThreshold))).toBe(30);
  });

  it("falls back to the default when absent", () => {
    expect(readNotificationThreshold(JSON.stringify(response))).toBe(10);
  });
});

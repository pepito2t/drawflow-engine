import { describe, expect, it } from "vitest";
import { describeFields } from "./form-schema";
import { importedFormValues, SettingsTransferError } from "./settings-transfer";
import type { SettingsSection } from "./settings";

const section: SettingsSection = {
  id: "dwg-parts",
  title: "Liste de pièces",
  fields: describeFields({
    properties: {
      included_blocks: { title: "Blocs", "x-ui": "text" },
      columns: { title: "Colonnes", "x-ui": "mapping" },
    },
  }),
  values: {},
  error: null,
};

describe("importedFormValues", () => {
  it("maps imported values onto the section fields", () => {
    const raw = JSON.stringify({
      section: "dwg-parts",
      title: "Liste de pièces",
      values: { included_blocks: "PANNEAU*", columns: [{ key: "Réf", value: "REF" }] },
    });

    expect(importedFormValues(raw, section)).toEqual({
      included_blocks: "PANNEAU*",
      columns: [{ key: "Réf", value: "REF" }],
    });
  });

  it("refuses a file made for another category", () => {
    const raw = JSON.stringify({ section: "pdf-report", title: "Rapport", values: {} });

    expect(() => importedFormValues(raw, section)).toThrow(SettingsTransferError);
  });
});

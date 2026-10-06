import { describe, expect, it } from "vitest";
import type { RunProposal } from "./assistant-chat";
import type { FieldDescriptor } from "./form-schema";
import { describeInputs, describeSynonyms, proposalTitle } from "./proposals";

const field = (name: string, label: string): FieldDescriptor => ({
  name,
  label,
  description: null,
  kind: "text",
  required: false,
  options: [],
  defaultValue: "",
  mappingLabels: null,
});

describe("describeInputs", () => {
  it("labels the inputs that carry a value and skips the empty ones", () => {
    const fields = [field("folders", "Dossiers"), field("output_folder", "Dossier de sortie")];

    expect(
      describeInputs(
        {
          files: [],
          folders: ["C:\\Plans\\Nord", "C:\\Plans\\Sud"],
          recursive: true,
          project: "",
          output_folder: "C:\\Sortie",
        },
        fields,
      ),
    ).toEqual([
      { label: "Dossiers", value: "C:\\Plans\\Nord, C:\\Plans\\Sud" },
      { label: "recursive", value: "oui" },
      { label: "Dossier de sortie", value: "C:\\Sortie" },
    ]);
  });
});

describe("proposalTitle", () => {
  it("names the preset when the proposal is one", () => {
    const base: RunProposal = {
      id: "c1",
      kind: "preset",
      feature: "soumission",
      featureName: "Soumission",
      label: "Chantier Nord",
      presetId: "ab12",
      inputs: {},
      status: "pending",
      error: null,
    };

    expect(proposalTitle(base)).toBe("Soumission — préréglage « Chantier Nord »");
    expect(proposalTitle({ ...base, kind: "feature", label: "Soumission" })).toBe("Soumission");
  });
});

describe("synonyms proposals", () => {
  it("lists the new header names per column and titles the card as a settings change", () => {
    const inputs = { columns: { Quantité: ["Nbre", "Qty"], Total: [] } };

    expect(describeSynonyms(inputs)).toEqual([{ label: "Quantité", value: "Nbre, Qty" }]);
    expect(
      proposalTitle({
        id: "p1",
        kind: "synonyms",
        feature: "soumission",
        featureName: "Soumission",
        label: "En-têtes reconnus",
        presetId: null,
        inputs,
        status: "pending",
        error: null,
      }),
    ).toBe("Ajouter des en-têtes reconnus (Soumission)");
  });
});

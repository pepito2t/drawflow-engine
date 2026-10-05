import { describe, expect, it } from "vitest";
import { parseGuide, sectionForAnchor } from "./guide";

const SECTIONS = parseGuide(
  JSON.stringify({
    sections: [
      { id: "premiers-pas", title: "Premiers pas", markdown: "1. Installer" },
      {
        id: "lancer-une-fonctionnalité",
        title: "Lancer une fonctionnalité",
        markdown: "Texte\n\n### Adapter une fonctionnalité à votre norme\n\nDétails",
      },
    ],
  }),
);

describe("sectionForAnchor", () => {
  it("finds a section by its anchor", () => {
    expect(sectionForAnchor(SECTIONS, "#premiers-pas")?.title).toBe("Premiers pas");
  });

  it("finds the section holding a sub-title", () => {
    expect(sectionForAnchor(SECTIONS, "#adapter-une-fonctionnalité-à-votre-norme")?.id).toBe(
      "lancer-une-fonctionnalité",
    );
  });

  it("returns nothing for an unknown anchor", () => {
    expect(sectionForAnchor(SECTIONS, "#fusée")).toBeNull();
  });
});

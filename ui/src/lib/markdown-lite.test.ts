import { describe, expect, it } from "vitest";
import { parseInlines, parseMarkdown, slug } from "./markdown-lite";

describe("parseMarkdown", () => {
  it("joins wrapped lines into one paragraph and splits on blank lines", () => {
    expect(parseMarkdown("\n\nPremière ligne\nsuite.\n\nDeuxième.")).toEqual([
      { kind: "paragraph", inlines: [{ kind: "text", text: "Première ligne suite." }] },
      { kind: "paragraph", inlines: [{ kind: "text", text: "Deuxième." }] },
    ]);
  });

  it("reads bullet and numbered lists", () => {
    expect(parseMarkdown("- un\n* deux\n\n1. premier\n2) second")).toEqual([
      {
        kind: "list",
        ordered: false,
        items: [
          { inlines: [{ kind: "text", text: "un" }], children: [] },
          { inlines: [{ kind: "text", text: "deux" }], children: [] },
        ],
      },
      {
        kind: "list",
        ordered: true,
        items: [
          { inlines: [{ kind: "text", text: "premier" }], children: [] },
          { inlines: [{ kind: "text", text: "second" }], children: [] },
        ],
      },
    ]);
  });

  it("keeps fenced code verbatim, even when unterminated while streaming", () => {
    expect(parseMarkdown('```json\n{ "a": 1 }\n```')).toEqual([
      { kind: "code", text: '{ "a": 1 }' },
    ]);
    expect(parseMarkdown("```\nen cours")).toEqual([{ kind: "code", text: "en cours" }]);
  });

  it("reads headings and a list right after a paragraph", () => {
    expect(parseMarkdown("## Titre\nTexte :\n- point")).toEqual([
      { kind: "heading", id: "titre", inlines: [{ kind: "text", text: "Titre" }] },
      { kind: "paragraph", inlines: [{ kind: "text", text: "Texte :" }] },
      {
        kind: "list",
        ordered: false,
        items: [{ inlines: [{ kind: "text", text: "point" }], children: [] }],
      },
    ]);
  });
});

describe("guide constructs", () => {
  it("nests indented steps under their parent step", () => {
    const [list] = parseMarkdown(
      "1. **Installer**\n2. Régler :\n   1. ODA\n   2. Ollama\n3. Lancer",
    );

    expect(list).toMatchObject({
      kind: "list",
      ordered: true,
      items: [
        { children: [] },
        { children: [[{ text: "ODA" }], [{ text: "Ollama" }]] },
        { inlines: [{ text: "Lancer" }] },
      ],
    });
  });

  it("reads pipe tables", () => {
    expect(parseMarkdown("| Prérequis | Rôle |\n|---|---|\n| ODA | Lire les **DWG** |")).toEqual([
      {
        kind: "table",
        header: [[{ kind: "text", text: "Prérequis" }], [{ kind: "text", text: "Rôle" }]],
        rows: [
          [
            [{ kind: "text", text: "ODA" }],
            [
              { kind: "text", text: "Lire les " },
              { kind: "strong", text: "DWG" },
            ],
          ],
        ],
      },
    ]);
  });

  it("reads links and builds the same anchors as GitHub", () => {
    expect(parseInlines("Voir [le guide](#utiliser-lassistant).")).toEqual([
      { kind: "text", text: "Voir " },
      { kind: "link", text: "le guide", href: "#utiliser-lassistant" },
      { kind: "text", text: "." },
    ]);
    expect(slug("Utiliser l'assistant")).toBe("utiliser-lassistant");
    expect(slug("Adapter une fonctionnalité à votre norme")).toBe(
      "adapter-une-fonctionnalité-à-votre-norme",
    );
  });
});

describe("parseInlines", () => {
  it("extracts bold and code spans and leaves HTML as plain text", () => {
    expect(parseInlines("**Liste** via `dwg-parts` <b>x</b>")).toEqual([
      { kind: "strong", text: "Liste" },
      { kind: "text", text: " via " },
      { kind: "code", text: "dwg-parts" },
      { kind: "text", text: " <b>x</b>" },
    ]);
  });
});

import { describe, expect, it } from "vitest";
import { parseInlines, parseMarkdown } from "./markdown-lite";

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
        items: [[{ kind: "text", text: "un" }], [{ kind: "text", text: "deux" }]],
      },
      {
        kind: "list",
        ordered: true,
        items: [[{ kind: "text", text: "premier" }], [{ kind: "text", text: "second" }]],
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
      { kind: "heading", inlines: [{ kind: "text", text: "Titre" }] },
      { kind: "paragraph", inlines: [{ kind: "text", text: "Texte :" }] },
      { kind: "list", ordered: false, items: [[{ kind: "text", text: "point" }]] },
    ]);
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

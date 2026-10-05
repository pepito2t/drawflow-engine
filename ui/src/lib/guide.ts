import { z } from "zod";
import { CatalogError } from "./catalog";
import { parseJsonOrNull } from "./json";
import { slug } from "./markdown-lite";

const guideSchema = z.object({
  sections: z.array(z.object({ id: z.string(), title: z.string(), markdown: z.string() })),
});

export type GuideSection = z.infer<typeof guideSchema>["sections"][number];

export function parseGuide(rawJson: string): GuideSection[] {
  const parsed = guideSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success || parsed.data.sections.length === 0) {
    throw new CatalogError("Le guide reçu du moteur est invalide.");
  }
  return parsed.data.sections;
}

/** The section to show for an anchor: a section itself, or the section holding that sub-title. */
export function sectionForAnchor(sections: GuideSection[], anchor: string): GuideSection | null {
  const id = anchor.replace(/^#/, "");
  return (
    sections.find((section) => section.id === id) ??
    sections.find((section) =>
      section.markdown
        .split("\n")
        .some((line) => /^#{3,6}\s/.test(line) && slug(line.replace(/^#+\s+/, "")) === id),
    ) ??
    null
  );
}

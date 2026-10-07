import { t } from "../i18n/settings";
import { z } from "zod";
import { CatalogError } from "./catalog";
import { parseJsonOrNull } from "./json";

const kindSchema = z.enum(["xlsx", "docx"]);

const librarySchema = z.object({
  templates: z.array(z.object({ id: z.string(), kind: kindSchema })),
  modules: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      kind: kindSchema,
      default: z.string().nullable(),
    }),
  ),
});

export type TemplateLibrary = z.infer<typeof librarySchema>;
export type TemplateKind = z.infer<typeof kindSchema>;

export function templateFileFilters(): { name: string; extensions: string[] }[] {
  return [{ name: t("templates.filter"), extensions: ["xlsx", "docx"] }];
}

export function parseTemplateLibrary(rawJson: string): TemplateLibrary {
  const parsed = librarySchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError(t("templates.invalidList"));
  }
  return parsed.data;
}

export function templatesOfKind(library: TemplateLibrary, kind: TemplateKind): string[] {
  return library.templates
    .filter((template) => template.kind === kind)
    .map((template) => template.id);
}

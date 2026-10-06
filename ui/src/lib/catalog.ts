import { t } from "../i18n/shell";
import { z } from "zod";
import { parseJsonOrNull } from "./json";
import { describeFields, inputsSchemaSchema, type FieldDescriptor } from "./form-schema";

export const MODULE_ICONS = ["module", "list", "report", "table", "check", "diff"] as const;
export type ModuleIconName = (typeof MODULE_ICONS)[number];

const manifestSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  version: z.string(),
  order: z.number().int(),
  instructions: z.array(z.string()),
  icon: z.enum(MODULE_ICONS).catch("module"),
});

const catalogSchema = z.array(z.object({ manifest: manifestSchema, inputs_schema: z.unknown() }));

export type ModuleManifest = z.infer<typeof manifestSchema>;

export interface CatalogModule {
  manifest: ModuleManifest;
  fields: FieldDescriptor[];
}

export class CatalogError extends Error {
  override name = "CatalogError";
}

export function parseCatalog(rawJson: string): CatalogModule[] {
  const parsed = catalogSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError(t("catalog.invalidList"));
  }
  return parsed.data.map(({ manifest, inputs_schema }) => ({
    manifest,
    fields: parseFormFields(t("catalog.moduleOwner", { id: manifest.id }), inputs_schema),
  }));
}

export function parseFormFields(owner: string, rawSchema: unknown): FieldDescriptor[] {
  const parsed = inputsSchemaSchema.safeParse(rawSchema);
  if (!parsed.success) {
    throw new CatalogError(t("catalog.invalidForm", { owner }));
  }
  return describeFields(parsed.data);
}

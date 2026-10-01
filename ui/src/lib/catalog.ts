import { z } from "zod";
import { parseJsonOrNull } from "./json";
import { describeFields, inputsSchemaSchema, type FieldDescriptor } from "./form-schema";

const manifestSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  version: z.string(),
  order: z.number().int(),
  instructions: z.array(z.string()),
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
    throw new CatalogError("La liste des fonctionnalités reçue du moteur est invalide.");
  }
  return parsed.data.map(({ manifest, inputs_schema }) => ({
    manifest,
    fields: describeFields(parseInputsSchema(manifest.id, inputs_schema)),
  }));
}

function parseInputsSchema(moduleId: string, rawSchema: unknown) {
  const parsed = inputsSchemaSchema.safeParse(rawSchema);
  if (!parsed.success) {
    throw new CatalogError(`Le formulaire du module « ${moduleId} » est invalide.`);
  }
  return parsed.data;
}

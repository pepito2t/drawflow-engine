import { z } from "zod";
import { CatalogError } from "./catalog";
import { initialValues, toFormValue, type FieldDescriptor, type FormValues } from "./form-schema";
import { parseJsonOrNull } from "./json";

const presetSchema = z.object({
  id: z.string(),
  name: z.string(),
  module: z.string(),
  inputs: z.record(z.string(), z.unknown()),
});

const presetsResponseSchema = z.object({ presets: z.array(presetSchema) });

export type Preset = z.infer<typeof presetSchema>;

export function parsePresets(rawJson: string): Preset[] {
  const parsed = presetsResponseSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError("La liste des préréglages reçue du moteur est invalide.");
  }
  return parsed.data.presets;
}

export function presetsFor(presets: Preset[], moduleId: string): Preset[] {
  return presets
    .filter((preset) => preset.module === moduleId)
    .sort((left, right) => left.name.localeCompare(right.name, "fr"));
}

/** Fields missing from an older preset fall back to the form defaults. */
export function presetFormValues(preset: Preset, fields: FieldDescriptor[]): FormValues {
  const defaults = initialValues(fields);
  return Object.fromEntries(
    fields.map((field) => [
      field.name,
      field.name in preset.inputs
        ? toFormValue(field.kind, preset.inputs[field.name])
        : (defaults[field.name] ?? ""),
    ]),
  );
}

import { t } from "../i18n/shell";
import { z } from "zod";
import { CatalogError } from "./catalog";
import { initialValues, toFormValue, type FieldDescriptor, type FormValues } from "./form-schema";
import { parseJsonOrNull } from "./json";
import { currentLanguage } from "../i18n";

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
    throw new CatalogError(t("presets.invalid"));
  }
  return parsed.data.presets;
}

export function presetsFor(presets: Preset[], moduleId: string): Preset[] {
  return presets
    .filter((preset) => preset.module === moduleId)
    .sort((left, right) => left.name.localeCompare(right.name, currentLanguage()));
}

export function presetFormValues(preset: Preset, fields: FieldDescriptor[]): FormValues {
  return formValuesFrom(preset.inputs, fields);
}

/** Fields missing from the inputs (older preset, assistant proposal) fall back to the defaults. */
export function formValuesFrom(
  inputs: Record<string, unknown>,
  fields: FieldDescriptor[],
): FormValues {
  const defaults = initialValues(fields);
  return Object.fromEntries(
    fields.map((field) => [
      field.name,
      field.name in inputs
        ? toFormValue(field.kind, inputs[field.name])
        : (defaults[field.name] ?? ""),
    ]),
  );
}

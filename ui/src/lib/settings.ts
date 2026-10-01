import { z } from "zod";
import { CatalogError, parseFormFields } from "./catalog";
import { toEngineInputs, toFormValue, type FieldDescriptor, type FormValues } from "./form-schema";
import { parseJsonOrNull } from "./json";

const settingsResponseSchema = z.object({
  sections: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      schema: z.unknown(),
      values: z.record(z.string(), z.unknown()),
      error: z.string().nullable(),
    }),
  ),
});

export interface SettingsSection {
  id: string;
  title: string;
  fields: FieldDescriptor[];
  values: FormValues;
  error: string | null;
}

export type SettingsValues = Record<string, FormValues>;

export function parseSettings(rawJson: string): SettingsSection[] {
  const parsed = settingsResponseSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError("Les paramètres reçus du moteur sont invalides.");
  }
  return parsed.data.sections.map((section) => {
    const fields = parseFormFields(`paramètre « ${section.title} »`, section.schema);
    return {
      id: section.id,
      title: section.title,
      fields,
      values: Object.fromEntries(
        fields.map((field) => [field.name, toFormValue(field.kind, section.values[field.name])]),
      ),
      error: section.error,
    };
  });
}

export function valuesBySection(sections: SettingsSection[]): SettingsValues {
  return Object.fromEntries(sections.map((section) => [section.id, section.values]));
}

export function toSettingsPayload(
  sections: SettingsSection[],
  values: SettingsValues,
): SettingsValues {
  return Object.fromEntries(
    sections.map((section) => [
      section.id,
      toEngineInputs(section.fields, values[section.id] ?? {}),
    ]),
  );
}

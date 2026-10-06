import { t } from "../i18n/settings";
import { z } from "zod";
import { DEFAULT_LANGUAGE, isLanguage, type Language } from "../i18n";
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
    throw new CatalogError(t("settings.invalidResponse"));
  }
  return parsed.data.sections.map((section) => {
    const fields = parseFormFields(
      t("settings.sectionLabel", { title: section.title }),
      section.schema,
    );
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

const GENERAL_SECTION_ID = "general";
const LANGUAGE_FIELD = "language";
const NOTIFICATION_THRESHOLD_FIELD = "notification_threshold_seconds";
const DEFAULT_NOTIFICATION_THRESHOLD_SECONDS = 10;

export function readLanguage(rawJson: string): Language {
  const general = parseSettings(rawJson).find((section) => section.id === GENERAL_SECTION_ID);
  const value = general?.values[LANGUAGE_FIELD];
  return isLanguage(value) ? value : DEFAULT_LANGUAGE;
}

export function readNotificationThreshold(rawJson: string): number {
  const general = parseSettings(rawJson).find((section) => section.id === GENERAL_SECTION_ID);
  const threshold = Number(general?.values[NOTIFICATION_THRESHOLD_FIELD]);
  return Number.isFinite(threshold) ? threshold : DEFAULT_NOTIFICATION_THRESHOLD_SECONDS;
}

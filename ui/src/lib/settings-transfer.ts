import { t } from "../i18n/settings";
import { z } from "zod";
import { toFormValue, type FormValues } from "./form-schema";
import { parseJsonOrNull } from "./json";
import type { SettingsSection } from "./settings";

const importSchema = z.object({
  section: z.string(),
  title: z.string(),
  values: z.record(z.string(), z.unknown()),
});

export class SettingsTransferError extends Error {
  override name = "SettingsTransferError";
}

export function settingsFileFilters(): { name: string; extensions: string[] }[] {
  return [{ name: t("transfer.filter"), extensions: ["json"] }];
}
export const SETTINGS_FILE_SUFFIX = ".drawflow.json";

/** Turns a validated import into form values for the section being edited. */
export function importedFormValues(rawJson: string, section: SettingsSection): FormValues {
  const parsed = importSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new SettingsTransferError(t("transfer.invalidResponse"));
  }
  if (parsed.data.section !== section.id) {
    throw new SettingsTransferError(
      t("transfer.wrongSection", { found: parsed.data.title, expected: section.title }),
    );
  }
  return Object.fromEntries(
    section.fields.map((field) => [
      field.name,
      toFormValue(field.kind, parsed.data.values[field.name]),
    ]),
  );
}

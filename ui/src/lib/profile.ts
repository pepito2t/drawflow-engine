import { t } from "../i18n/settings";
import { z } from "zod";
import { parseJsonOrNull } from "./json";

const profilePreviewSchema = z.object({
  app_version: z.string(),
  exported_at: z.string().nullable(),
  sections: z.array(z.object({ id: z.string(), title: z.string() })),
  presets: z.array(z.string()),
  templates: z.array(z.string()),
  replaced_presets: z.number().int().nonnegative(),
  replaced_templates: z.array(z.string()),
});

export type ProfilePreview = z.infer<typeof profilePreviewSchema>;

export class ProfileError extends Error {
  override name = "ProfileError";
}

export function profileFileFilters(): { name: string; extensions: string[] }[] {
  return [{ name: t("profile.filter"), extensions: ["zip"] }];
}
export const PROFILE_FILE_SUFFIX = ".drawflow-profil.zip";

export function parseProfilePreview(rawJson: string): ProfilePreview {
  const parsed = profilePreviewSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new ProfileError(t("profile.invalidResponse"));
  }
  return parsed.data;
}

/** One sentence per thing the import touches, so the user knows what is overwritten. */
export function describeProfileChanges(preview: ProfilePreview): string[] {
  const lines = [
    t("profile.sectionsReplaced", {
      count: preview.sections.length,
      titles: preview.sections.map((section) => section.title).join(", "),
    }),
  ];
  const presetsLine =
    preview.replaced_presets > 0
      ? t("profile.presetsReplacing", {
          count: preview.presets.length,
          replaced: preview.replaced_presets,
        })
      : t("profile.presetsImported", { count: preview.presets.length });
  lines.push(presetsLine);
  const replaced =
    preview.replaced_templates.length > 0
      ? t("profile.templatesReplaced", { names: preview.replaced_templates.join(", ") })
      : "";
  lines.push(t("profile.templatesImported", { count: preview.templates.length, replaced }));
  return lines;
}

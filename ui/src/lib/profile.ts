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

export const PROFILE_FILE_FILTERS = [{ name: "Profil Drawflow", extensions: ["zip"] }];
export const PROFILE_FILE_SUFFIX = ".drawflow-profil.zip";

export function parseProfilePreview(rawJson: string): ProfilePreview {
  const parsed = profilePreviewSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new ProfileError("Réponse du moteur invalide pour le profil.");
  }
  return parsed.data;
}

/** One sentence per thing the import touches, so the user knows what is overwritten. */
export function describeProfileChanges(preview: ProfilePreview): string[] {
  const lines = [
    `${String(preview.sections.length)} catégories de paramètres remplacées : ${preview.sections
      .map((section) => section.title)
      .join(", ")}.`,
  ];
  const presetsLine =
    preview.replaced_presets > 0
      ? `${String(preview.presets.length)} préréglages importés ; les ${String(preview.replaced_presets)} préréglages actuels sont supprimés.`
      : `${String(preview.presets.length)} préréglages importés.`;
  lines.push(presetsLine);
  const replaced =
    preview.replaced_templates.length > 0
      ? ` (${preview.replaced_templates.join(", ")} remplacés)`
      : "";
  lines.push(`${String(preview.templates.length)} modèles importés${replaced}.`);
  return lines;
}

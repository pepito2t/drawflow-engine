import type { CatalogModule } from "./catalog";
import { isFolderKind, isPathKind, type FieldDescriptor } from "./form-schema";
import type { Preset } from "./presets";
import type { Automation } from "./tauri/automations";

const ID_LENGTH = 8;

export function newAutomation(): Automation {
  return {
    id: crypto.randomUUID().replaceAll("-", "").slice(0, ID_LENGTH),
    folder: "",
    presetId: "",
    enabled: true,
  };
}

/** The watched file replaces the preset's plan input; everything else comes from the preset. */
export function inputsForNewFile(
  fields: FieldDescriptor[],
  presetInputs: Record<string, unknown>,
  path: string,
): Record<string, unknown> {
  const target = fields.find((field) => isPathKind(field.kind) && !isFolderKind(field.kind));
  if (!target) {
    throw new Error("Cette fonctionnalité ne prend pas de fichier en entrée.");
  }
  const value = target.kind === "files" ? [path] : path;
  return { ...presetInputs, [target.name]: value };
}

export function describePresetTarget(preset: Preset, modules: CatalogModule[]): string {
  const moduleName = modules.find((module) => module.manifest.id === preset.module)?.manifest.name;
  return moduleName ? `${preset.name} — ${moduleName}` : preset.name;
}

export function validateAutomations(automations: Automation[], presets: Preset[]): string | null {
  for (const automation of automations) {
    if (!automation.folder.trim()) {
      return "Chaque automatisation doit surveiller un dossier.";
    }
    if (!presets.some((preset) => preset.id === automation.presetId)) {
      return "Chaque automatisation doit lancer un préréglage existant.";
    }
  }
  return null;
}

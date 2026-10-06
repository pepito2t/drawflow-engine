import { t } from "../i18n/settings";
import { z } from "zod";
import { CatalogError } from "./catalog";
import { parseJsonOrNull } from "./json";
import { dateLocale } from "../i18n/panels";

const catalogSchema = z.object({
  memory_gb: z.number().nullable(),
  recommended: z.string(),
  configured: z.string(),
  server_url: z.string(),
  is_ollama: z.boolean(),
  models: z.array(
    z.object({
      name: z.string(),
      label: z.string(),
      size_gb: z.number(),
      min_memory_gb: z.number().nullable(),
      description: z.string(),
      installed: z.boolean(),
    }),
  ),
});

export type ModelCatalog = z.infer<typeof catalogSchema>;
export type CatalogEntry = ModelCatalog["models"][number];

export const OLLAMA_LIBRARY_URL = "https://ollama.com/library";

export function parseModelCatalog(rawJson: string): ModelCatalog {
  const parsed = catalogSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError(t("models.invalidCatalog"));
  }
  return parsed.data;
}

/** Recommended first, then installed, then the rest in catalog order. */
export function visibleModels(catalog: ModelCatalog, query: string): CatalogEntry[] {
  const needle = normalize(query);
  const matches = catalog.models.filter(
    (model) =>
      needle === "" ||
      [model.name, model.label, model.description].some((text) => normalize(text).includes(needle)),
  );
  return [...matches].sort((a, b) => rank(catalog, a) - rank(catalog, b));
}

export function fitsInMemory(catalog: ModelCatalog, model: CatalogEntry): boolean {
  return (
    catalog.memory_gb === null ||
    model.min_memory_gb === null ||
    model.min_memory_gb <= catalog.memory_gb
  );
}

export function formatSize(sizeGb: number): string {
  return t("models.size", {
    size: sizeGb.toLocaleString(dateLocale(), { maximumFractionDigits: 1 }),
  });
}

function rank(catalog: ModelCatalog, model: CatalogEntry): number {
  if (model.name === catalog.recommended) {
    return 0;
  }
  return model.installed ? 1 : 2;
}

function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

import { CatalogError } from "./catalog";

export interface ReadableError {
  message: string;
  hint: string | null;
}

const FALLBACK_MESSAGE = "Une erreur inattendue est survenue.";
const ENGINE_START_HINT =
  "Vérifiez que l'application est correctement installée, puis réessayez. Si le problème persiste, réinstallez la dernière version.";

export function toReadableError(error: unknown): ReadableError {
  if (error instanceof CatalogError) {
    return { message: error.message, hint: "Mettez l'application à jour puis réessayez." };
  }
  if (typeof error === "string") {
    return { message: error, hint: ENGINE_START_HINT };
  }
  if (error instanceof Error) {
    return { message: error.message, hint: ENGINE_START_HINT };
  }
  return { message: FALLBACK_MESSAGE, hint: ENGINE_START_HINT };
}

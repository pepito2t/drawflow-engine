import { t } from "../i18n/shell";
import { CatalogError } from "./catalog";
import { EngineCommandError } from "./engine-output";
import { parseBridgeError, translateBridgeError } from "./tauri/bridge-error";

export interface ReadableError {
  message: string;
  hint: string | null;
  file: string | null;
}

export function toReadableError(error: unknown): ReadableError {
  if (error instanceof EngineCommandError) {
    return { message: error.message, hint: error.hint, file: error.file };
  }
  if (error instanceof CatalogError) {
    return { message: error.message, hint: t("errorMessage.updateHint"), file: null };
  }
  const bridgeError = parseBridgeError(error);
  if (bridgeError) {
    return { message: translateBridgeError(bridgeError), hint: null, file: null };
  }
  if (typeof error === "string") {
    return { message: error, hint: t("errorMessage.engineStartHint"), file: null };
  }
  if (error instanceof Error) {
    return { message: error.message, hint: t("errorMessage.engineStartHint"), file: null };
  }
  return {
    message: t("errorMessage.unexpected"),
    hint: t("errorMessage.engineStartHint"),
    file: null,
  };
}

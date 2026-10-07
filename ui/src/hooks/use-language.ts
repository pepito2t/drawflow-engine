import { useSyncExternalStore } from "react";
import { currentLanguage, onLanguageChange, type Language } from "../i18n";

/** Re-renders the caller when the language changes; its catalog strings are resolved at render. */
export function useLanguage(): Language {
  return useSyncExternalStore(onLanguageChange, currentLanguage);
}

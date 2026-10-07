import { useEffect } from "react";
import { setLanguage } from "../i18n";
import { readLanguage } from "../lib/settings";
import { useSettingsFeed } from "./settings-feed";

/** The language lives in the engine's settings; the UI follows it at start and after each save. */
export function useLanguageSync(): void {
  const { latest, subscribe } = useSettingsFeed();
  useEffect(() => {
    const apply = (rawSettings: string) => {
      try {
        setLanguage(readLanguage(rawSettings));
      } catch (error: unknown) {
        console.error("Langue non lue depuis les paramètres :", error);
      }
    };
    const current = latest();
    if (current !== null) {
      apply(current);
    }
    return subscribe(apply);
  }, [latest, subscribe]);
}

import { useEffect } from "react";
import { setLanguage } from "../i18n";
import { readLanguage } from "../lib/settings";
import { getSettings } from "../lib/tauri/engine";
import { useNotificationCenter } from "./notification-center";

/** The language lives in the engine's settings; the UI follows it at start and after each save. */
export function useLanguageSync(): void {
  const { subscribe } = useNotificationCenter();
  useEffect(() => {
    const apply = () => {
      getSettings()
        .then((raw) => {
          setLanguage(readLanguage(raw));
        })
        .catch((error: unknown) => {
          console.error("Langue non lue depuis les paramètres :", error);
        });
    };
    apply();
    return subscribe((event) => {
      if (event.type === "settingsSaved") {
        apply();
      }
    });
  }, [subscribe]);
}

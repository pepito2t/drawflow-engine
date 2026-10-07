import { useEffect, useRef, useState } from "react";
import { parseCatalog, type CatalogModule } from "../lib/catalog";
import { listModules } from "../lib/tauri/engine";
import { useLanguage } from "./use-language";

export function loadCatalog(): Promise<CatalogModule[]> {
  return listModules().then(parseCatalog);
}

/** Module names and labels come from the engine: the catalog follows the language in place. */
export function useModuleCatalog(initialModules: CatalogModule[]): CatalogModule[] {
  const language = useLanguage();
  const [modules, setModules] = useState(initialModules);
  const loadedLanguage = useRef(language);

  useEffect(() => {
    if (loadedLanguage.current === language) {
      return;
    }
    let superseded = false;
    loadCatalog()
      .then((fresh) => {
        if (!superseded) {
          loadedLanguage.current = language;
          setModules(fresh);
        }
      })
      .catch((error: unknown) => {
        console.error("Catalogue non rechargé après le changement de langue :", error);
      });
    return () => {
      superseded = true;
    };
  }, [language]);

  return modules;
}

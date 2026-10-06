import { createContext, use, useEffect, useState, type ReactNode } from "react";
import {
  currentLanguage,
  detectLanguage,
  onLanguageChange,
  setLanguage,
  type Language,
} from "../i18n";

const LanguageContext = createContext<Language>(currentLanguage());

/** Re-renders the whole tree when the language changes: every string is resolved at render. */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setCurrent] = useState<Language>(() => {
    setLanguage(detectLanguage());
    return currentLanguage();
  });
  useEffect(() => onLanguageChange(setCurrent), []);
  return (
    <LanguageContext value={language}>
      <div key={language} className="language-root">
        {children}
      </div>
    </LanguageContext>
  );
}

export function useLanguage(): Language {
  return use(LanguageContext);
}

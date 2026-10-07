export type Language = "fr" | "en";

export const LANGUAGES: readonly Language[] = ["fr", "en"];
export const DEFAULT_LANGUAGE: Language = "fr";
const STORAGE_KEY = "drawflow.language";
const PLACEHOLDER = /\{(\w+)\}/g;

let current: Language = DEFAULT_LANGUAGE;
const listeners = new Set<(language: Language) => void>();

export function isLanguage(value: unknown): value is Language {
  return typeof value === "string" && (LANGUAGES as readonly string[]).includes(value);
}

export function currentLanguage(): Language {
  return current;
}

export function setLanguage(language: Language): void {
  applyDocumentLanguage(language);
  if (language === current) {
    return;
  }
  current = language;
  try {
    localStorage.setItem(STORAGE_KEY, language);
  } catch {
    // Browser storage is a convenience only; the setting itself lives in the engine's settings.
  }
  for (const listener of listeners) {
    listener(language);
  }
}

function applyDocumentLanguage(language: Language): void {
  if (typeof document !== "undefined") {
    document.documentElement.lang = language;
  }
}

export function onLanguageChange(listener: (language: Language) => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Before the settings are readable (lock screen, first start): last choice, else the OS language. */
export function detectLanguage(): Language {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isLanguage(stored)) {
      return stored;
    }
  } catch {
    // Same as above: nothing stored is a normal case.
  }
  const system = typeof navigator === "undefined" ? "" : navigator.language.toLowerCase();
  return system.startsWith("fr") ? "fr" : system ? "en" : DEFAULT_LANGUAGE;
}

export type Params = Record<string, string | number>;

function interpolate(text: string, params: Params | undefined): string {
  if (!params) {
    return text;
  }
  return text.replace(PLACEHOLDER, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}

export interface Translate<Keys extends string> {
  (key: Keys, params?: Params): string;
  /** For keys built at run time, such as error codes received from Rust. */
  has: (key: string) => key is Keys;
}

/**
 * A catalog with the same keys in both languages; `t` resolves the current language at call time,
 * so plain functions and components use it alike. `{name}` placeholders take `params`.
 */
export function defineMessages<const Keys extends string>(messages: {
  fr: Record<Keys, string>;
  en: Record<Keys, string>;
}): Translate<Keys> {
  const translate = (key: Keys, params?: Params): string =>
    interpolate(messages[current][key], params);
  const has = (key: string): key is Keys => Object.hasOwn(messages.fr, key);
  return Object.assign(translate, { has });
}

/** `one` when count is 1, `other` otherwise; both may use `{count}`. */
export function plural(count: number, one: string, other: string): string {
  return interpolate(count === 1 ? one : other, { count });
}

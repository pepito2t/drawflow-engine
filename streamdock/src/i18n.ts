export type Language = "fr" | "en";

export const DEFAULT_LANGUAGE: Language = "fr";

const FR = {
  "face.offline": "Hors ligne",
  "face.locked": "Verrouillé",
  "face.refused": "Jeton invalide",
  "face.running": "En cours",
  "face.succeeded": "Terminé",
  "face.failed": "Échec",
  "face.cancelled": "Annulé",
  "key.preset.choose": "Choisir un préréglage",
  "key.preset.gone": "Préréglage supprimé",
  "key.tab.choose": "Choisir un onglet",
  "key.cancel": "Annuler",
  "key.runs": "Traitements",
  "key.runs.none": "Aucun",
  "key.runs.count": "{count} en cours",
  "key.lastResult": "Dernier résultat",
  "error.offline": "Drawflow n'est pas joignable (application fermée ou API locale désactivée).",
  "error.locked": "Drawflow est verrouillée : saisissez le code d'accès dans l'application.",
  "error.refused": "Jeton refusé par Drawflow : vérifiez le jeton dans les réglages de la touche.",
  "error.timeout": "Drawflow n'a pas répondu à temps.",
  "error.unknown": "Erreur inconnue.",
  "error.unreadableState": "Réponse de Drawflow illisible : mettez à jour le plugin.",
  "error.presetNotChosen": "Choisissez un préréglage dans les réglages de la touche",
  "error.presetGone": "Ce préréglage n'existe plus dans Drawflow",
  "error.tabNotChosen": "Choisissez un onglet dans les réglages de la touche",
} as const;

export type MessageKey = keyof typeof FR;

const EN: Record<MessageKey, string> = {
  "face.offline": "Offline",
  "face.locked": "Locked",
  "face.refused": "Invalid token",
  "face.running": "Running",
  "face.succeeded": "Done",
  "face.failed": "Failed",
  "face.cancelled": "Cancelled",
  "key.preset.choose": "Choose a preset",
  "key.preset.gone": "Preset deleted",
  "key.tab.choose": "Choose a tab",
  "key.cancel": "Cancel",
  "key.runs": "Runs",
  "key.runs.none": "None",
  "key.runs.count": "{count} running",
  "key.lastResult": "Last result",
  "error.offline": "Drawflow cannot be reached (application closed or local API disabled).",
  "error.locked": "Drawflow is locked: enter the access code in the application.",
  "error.refused": "Token refused by Drawflow: check the token in the key settings.",
  "error.timeout": "Drawflow did not answer in time.",
  "error.unknown": "Unknown error.",
  "error.unreadableState": "Unreadable answer from Drawflow: update the plugin.",
  "error.presetNotChosen": "Choose a preset in the key settings",
  "error.presetGone": "This preset no longer exists in Drawflow",
  "error.tabNotChosen": "Choose a tab in the key settings",
};

const MESSAGES: Record<Language, Record<MessageKey, string>> = { fr: FR, en: EN };

export function translate(
  language: Language,
  key: MessageKey,
  params: Record<string, string> = {},
): string {
  return Object.entries(params).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, value),
    MESSAGES[language][key],
  );
}

/** Stream Dock passes its own language in `-info {"application":{"language":"en"}}`. */
export function languageFromInfo(info: string | undefined): Language {
  if (info === undefined) {
    return DEFAULT_LANGUAGE;
  }
  try {
    const parsed: unknown = JSON.parse(info);
    const language =
      isRecord(parsed) && isRecord(parsed.application) ? parsed.application.language : null;
    return typeof language === "string" && language.toLowerCase().startsWith("en")
      ? "en"
      : DEFAULT_LANGUAGE;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

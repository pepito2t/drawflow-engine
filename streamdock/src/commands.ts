import { translate, type Language, type MessageKey } from "./i18n";

/** A Drawflow command that needs no argument, so a single generic key can send it. */
export interface PluginCommand {
  id: string;
  label: MessageKey;
}

export interface CommandChoice {
  label: string;
  value: string;
}

/** Kept in sync with the argument-less commands of `ui/src/lib/commands.ts` by a test of the UI. */
export const PLUGIN_COMMANDS: readonly PluginCommand[] = [
  { id: "today.open", label: "command.today.open" },
  { id: "history.open", label: "command.history.open" },
  { id: "mail.open", label: "command.mail.open" },
  { id: "mail.fetch", label: "command.mail.fetch" },
  { id: "result.open-last", label: "command.result.open-last" },
  { id: "feature.run-current", label: "command.feature.run-current" },
  { id: "runs.cancel-all", label: "command.runs.cancel-all" },
  { id: "assistant.toggle", label: "command.assistant.toggle" },
  { id: "settings.open", label: "command.settings.open" },
  { id: "setup.open", label: "command.setup.open" },
  { id: "models.open", label: "command.models.open" },
  { id: "help.open", label: "command.help.open" },
  { id: "update.install", label: "command.update.install" },
];

export function commandLabel(language: Language, commandId: string): string | null {
  const found = PLUGIN_COMMANDS.find((command) => command.id === commandId);
  return found ? translate(language, found.label) : null;
}

export function commandChoices(language: Language): CommandChoice[] {
  return PLUGIN_COMMANDS.map((command) => ({
    label: translate(language, command.label),
    value: command.id,
  }));
}

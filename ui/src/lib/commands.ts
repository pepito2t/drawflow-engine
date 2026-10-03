import { z } from "zod";

/** Every UI action reachable from outside (Stream Deck, local LLM) is declared here. */
export const COMMAND_ARGUMENTS = {
  "tab.open": z.object({ moduleId: z.string().min(1) }),
  "preset.run": z.object({ presetId: z.string().min(1) }),
  "runs.cancel-all": z.object({}),
  "result.open-last": z.object({}),
  "settings.open": z.object({}),
  "assistant.toggle": z.object({}),
  "update.install": z.object({}),
  "app.state": z.object({}),
} as const;

export type CommandId = keyof typeof COMMAND_ARGUMENTS;
export type CommandArguments<Id extends CommandId> = z.infer<(typeof COMMAND_ARGUMENTS)[Id]>;
export type CommandHandler<Id extends CommandId> = (args: CommandArguments<Id>) => unknown;

export const COMMANDS = {
  openTab: "tab.open",
  runPreset: "preset.run",
  cancelAllRuns: "runs.cancel-all",
  openLastResult: "result.open-last",
  openSettings: "settings.open",
  toggleAssistant: "assistant.toggle",
  installUpdate: "update.install",
  appState: "app.state",
} as const satisfies Record<string, CommandId>;

export type CommandResult = { ok: true; data?: unknown } | { ok: false; error: string };

export function isCommandId(value: string): value is CommandId {
  return value in COMMAND_ARGUMENTS;
}

export function parseCommandArguments(
  id: string,
  raw: unknown,
): { ok: true; id: CommandId; args: unknown } | { ok: false; error: string } {
  if (!isCommandId(id)) {
    return { ok: false, error: `Commande inconnue : ${id}` };
  }
  const parsed = COMMAND_ARGUMENTS[id].safeParse(raw ?? {});
  if (!parsed.success) {
    return { ok: false, error: `Arguments invalides pour ${id}.` };
  }
  return { ok: true, id, args: parsed.data };
}

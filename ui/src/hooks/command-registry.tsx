import { t } from "../i18n/shell";
import { createContext, use, useCallback, useEffect, useMemo, useRef, type ReactNode } from "react";
import {
  parseCommandArguments,
  type CommandHandler,
  type CommandId,
  type CommandResult,
} from "../lib/commands";

type AnyHandler = (args: unknown) => unknown;

interface CommandRegistry {
  register: <Id extends CommandId>(id: Id, handler: CommandHandler<Id>) => () => void;
  execute: (id: string, args?: unknown) => Promise<CommandResult>;
}

const CommandContext = createContext<CommandRegistry | null>(null);

export function CommandProvider({ children }: { children: ReactNode }) {
  const handlers = useRef(new Map<CommandId, AnyHandler>());

  const register = useCallback(<Id extends CommandId>(id: Id, handler: CommandHandler<Id>) => {
    const stored = handler as AnyHandler;
    handlers.current.set(id, stored);
    return () => {
      if (handlers.current.get(id) === stored) {
        handlers.current.delete(id);
      }
    };
  }, []);

  const execute = useCallback(async (id: string, args?: unknown): Promise<CommandResult> => {
    const parsed = parseCommandArguments(id, args);
    if (!parsed.ok) {
      return parsed;
    }
    const handler = handlers.current.get(parsed.id);
    if (!handler) {
      return { ok: false, error: t("commands.unavailable", { id: parsed.id }) };
    }
    try {
      const data: unknown = await handler(parsed.args);
      return data === undefined ? { ok: true } : { ok: true, data };
    } catch (error: unknown) {
      return { ok: false, error: error instanceof Error ? error.message : String(error) };
    }
  }, []);

  const registry = useMemo(() => ({ register, execute }), [register, execute]);
  return <CommandContext value={registry}>{children}</CommandContext>;
}

export function useCommands(): CommandRegistry {
  const registry = use(CommandContext);
  if (registry === null) {
    throw new Error("useCommands doit être utilisé dans un CommandProvider.");
  }
  return registry;
}

export function useCommand<Id extends CommandId>(id: Id, handler: CommandHandler<Id>): void {
  const { register } = useCommands();
  useEffect(() => register(id, handler), [register, id, handler]);
}

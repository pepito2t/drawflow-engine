import { createContext, use, useCallback, useEffect, useMemo, useRef, type ReactNode } from "react";
import type { CommandHandler, CommandId } from "../lib/commands";

interface CommandRegistry {
  register: (id: CommandId, handler: CommandHandler) => () => void;
  execute: (id: CommandId) => boolean;
}

const CommandContext = createContext<CommandRegistry | null>(null);

export function CommandProvider({ children }: { children: ReactNode }) {
  const handlers = useRef(new Map<CommandId, CommandHandler>());

  const register = useCallback((id: CommandId, handler: CommandHandler) => {
    handlers.current.set(id, handler);
    return () => {
      if (handlers.current.get(id) === handler) {
        handlers.current.delete(id);
      }
    };
  }, []);

  const execute = useCallback((id: CommandId) => {
    const handler = handlers.current.get(id);
    if (!handler) {
      console.warn(`Commande indisponible : ${id}`);
      return false;
    }
    handler();
    return true;
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

export function useCommand(id: CommandId, handler: CommandHandler): void {
  const { register } = useCommands();
  useEffect(() => register(id, handler), [register, id, handler]);
}

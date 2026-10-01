/** Named commands: every UI action reachable from outside (Stream Deck, local LLM) goes here. */
export const COMMANDS = {
  installUpdate: "update.install",
} as const;

export type CommandId = (typeof COMMANDS)[keyof typeof COMMANDS];
export type CommandHandler = () => void;

import { COMMANDS, type CommandId } from "./commands";

export interface KeyPress {
  key: string;
  ctrlKey: boolean;
  altKey: boolean;
  shiftKey: boolean;
  metaKey: boolean;
}

interface Shortcut {
  key: string;
  ctrl: boolean;
  command: CommandId;
}

export const SHORTCUTS: readonly Shortcut[] = [
  { key: "Enter", ctrl: true, command: COMMANDS.runCurrentFeature },
  { key: ",", ctrl: true, command: COMMANDS.openSettings },
  { key: "F1", ctrl: false, command: COMMANDS.openHelp },
];

/** The command a key press triggers; extra modifiers never match, so OS and browser shortcuts stay. */
export function shortcutCommand(press: KeyPress): CommandId | null {
  if (press.altKey || press.shiftKey || press.metaKey) {
    return null;
  }
  const match = SHORTCUTS.find(
    (shortcut) => shortcut.key === press.key && shortcut.ctrl === press.ctrlKey,
  );
  return match?.command ?? null;
}

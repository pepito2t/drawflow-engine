import { describe, expect, it } from "vitest";
import { COMMANDS } from "./commands";
import { shortcutCommand, type KeyPress } from "./shortcuts";

const press = (key: string, modifiers: Partial<KeyPress> = {}): KeyPress => ({
  key,
  ctrlKey: false,
  altKey: false,
  shiftKey: false,
  metaKey: false,
  ...modifiers,
});

describe("shortcutCommand", () => {
  it("maps Ctrl+Enter, Ctrl+, and F1 to their commands", () => {
    expect(shortcutCommand(press("Enter", { ctrlKey: true }))).toBe(COMMANDS.runCurrentFeature);
    expect(shortcutCommand(press(",", { ctrlKey: true }))).toBe(COMMANDS.openSettings);
    expect(shortcutCommand(press("F1"))).toBe(COMMANDS.openHelp);
  });

  it("ignores the same keys without Ctrl or with other modifiers", () => {
    expect(shortcutCommand(press("Enter"))).toBeNull();
    expect(shortcutCommand(press("Enter", { ctrlKey: true, shiftKey: true }))).toBeNull();
    expect(shortcutCommand(press("F1", { ctrlKey: true }))).toBeNull();
    expect(shortcutCommand(press("a", { ctrlKey: true }))).toBeNull();
  });
});

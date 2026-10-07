import { describe, expect, it } from "vitest";
import { targetTabIndex } from "./tablist-navigation";

describe("targetTabIndex", () => {
  it("moves down and up, wrapping at both ends", () => {
    expect(targetTabIndex("ArrowDown", 0, 3)).toBe(1);
    expect(targetTabIndex("ArrowDown", 2, 3)).toBe(0);
    expect(targetTabIndex("ArrowUp", 1, 3)).toBe(0);
    expect(targetTabIndex("ArrowUp", 0, 3)).toBe(2);
  });

  it("jumps to the first and last tab", () => {
    expect(targetTabIndex("Home", 2, 3)).toBe(0);
    expect(targetTabIndex("End", 0, 3)).toBe(2);
  });

  it("ignores other keys and empty lists", () => {
    expect(targetTabIndex("Enter", 0, 3)).toBeNull();
    expect(targetTabIndex("ArrowDown", 0, 0)).toBeNull();
  });
});

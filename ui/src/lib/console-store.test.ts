import { describe, expect, it } from "vitest";
import type { ConsoleEntry } from "./console";
import { consoleReducer, INITIAL_CONSOLE_STATE } from "./console-store";

function error(id: number): ConsoleEntry {
  return { id, timestamp: 0, level: "error", source: "engine", message: "x" };
}

describe("consoleReducer", () => {
  it("counts new errors as unseen while the panel is closed", () => {
    const state = consoleReducer(INITIAL_CONSOLE_STATE, { type: "received", entries: [error(0)] });
    expect(state.lastSeenId).toBe(-1);
    expect(state.entries).toHaveLength(1);
  });

  it("marks everything seen on opening and while open", () => {
    const received = consoleReducer(INITIAL_CONSOLE_STATE, {
      type: "received",
      entries: [error(0), error(1)],
    });
    const opened = consoleReducer(received, { type: "panelToggled" });
    expect(opened).toMatchObject({ isPanelOpen: true, lastSeenId: 1 });
    const more = consoleReducer(opened, { type: "received", entries: [error(2)] });
    expect(more.lastSeenId).toBe(2);
    expect(consoleReducer(more, { type: "panelToggled" }).isPanelOpen).toBe(false);
  });

  it("closes the docked panel and marks entries seen when detaching", () => {
    const opened = consoleReducer(
      consoleReducer(INITIAL_CONSOLE_STATE, { type: "received", entries: [error(4)] }),
      { type: "panelToggled" },
    );
    expect(consoleReducer(opened, { type: "detached" })).toMatchObject({
      isPanelOpen: false,
      lastSeenId: 4,
    });
  });

  it("empties the list on clear and clears a load error on the next entries", () => {
    const failed = consoleReducer(INITIAL_CONSOLE_STATE, { type: "loadFailed", message: "Verrou" });
    expect(failed.loadError).toBe("Verrou");
    const received = consoleReducer(failed, { type: "received", entries: [error(0)] });
    expect(received.loadError).toBeNull();
    expect(consoleReducer(received, { type: "cleared" }).entries).toEqual([]);
  });
});

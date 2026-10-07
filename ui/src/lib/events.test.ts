import { describe, expect, it } from "vitest";
import { parseEventLine, unreadableEventMessage } from "./events";

describe("parseEventLine", () => {
  it("parses a valid progress event", () => {
    const line = '{"type":"progress","current":1,"total":4,"message":"Plan é.dwg"}';

    expect(parseEventLine(line)).toEqual({
      type: "progress",
      current: 1,
      total: 4,
      message: "Plan é.dwg",
    });
  });

  it("gives nothing for a line that is not JSON, so stray output is never an error", () => {
    expect(parseEventLine("not json")).toBeNull();
    expect(parseEventLine("")).toBeNull();
  });

  it("rejects unknown event types", () => {
    expect(parseEventLine('{"type":"surprise"}')).toBeNull();
  });

  it("rejects events missing required fields", () => {
    expect(parseEventLine('{"type":"progress","current":1}')).toBeNull();
  });

  it("keeps a readable message for unreadable assistant lines", () => {
    expect(unreadableEventMessage()).not.toBe("");
  });
});

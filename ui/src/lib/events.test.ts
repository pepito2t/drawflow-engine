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

  it("turns malformed JSON into a readable error event", () => {
    const event = parseEventLine("not json");

    expect(event).toMatchObject({
      type: "error",
      message: unreadableEventMessage(),
      hint: "not json",
    });
  });

  it("rejects unknown event types", () => {
    expect(parseEventLine('{"type":"surprise"}')).toMatchObject({
      type: "error",
      message: unreadableEventMessage(),
    });
  });

  it("rejects events missing required fields", () => {
    expect(parseEventLine('{"type":"progress","current":1}').type).toBe("error");
  });
});

import { describe, expect, it } from "vitest";
import {
  describeDuration,
  describeStart,
  lastOutput,
  parseHistory,
  type HistoryEntry,
} from "./history";

const ENTRY: HistoryEntry = {
  id: "abc123",
  started_at: "2026-10-06T08:30:00+00:00",
  module: "dwg-parts",
  module_name: "Liste de pièces",
  inputs: { files: ["C:\\Plans\\a.dwg"] },
  status: "succeeded",
  summary: "12 pièces",
  outputs: ["C:\\Sortie\\liste.xlsx"],
  warnings: [],
  error: null,
  duration_ms: 4200,
};

describe("history", () => {
  it("parses the engine's entries and rejects anything else", () => {
    expect(parseHistory(JSON.stringify({ entries: [ENTRY] }))[0]?.summary).toBe("12 pièces");
    expect(() => parseHistory('{"entries": [{"id": 1}]}')).toThrow("invalide");
  });

  it("describes durations in a readable form", () => {
    expect(describeDuration(300)).toBe("< 1 s");
    expect(describeDuration(4200)).toBe("4 s");
    expect(describeDuration(125000)).toBe("2 min 05 s");
  });

  it("shows only the time for today's runs", () => {
    const now = new Date("2026-10-06T10:00:00+00:00");

    expect(describeStart("2026-10-06T08:30:00+00:00", now)).not.toContain("06");
    expect(describeStart("2026-10-05T08:30:00+00:00", now)).toContain("05");
    expect(describeStart("pas une date", now)).toBe("pas une date");
  });

  it("gives the last produced file", () => {
    expect(lastOutput(ENTRY)).toBe("C:\\Sortie\\liste.xlsx");
    expect(lastOutput({ ...ENTRY, outputs: [] })).toBeNull();
  });
});

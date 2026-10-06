import { describe, expect, it } from "vitest";
import { formatSavedTime, parseUsageStats, totalsOf } from "./stats";

const RAW = JSON.stringify({
  since: "2026-10-06T08:00:00+00:00",
  features: [
    { module: "dwg-parts", module_name: "Liste de pièces", runs: 3, files: 12, minutes_saved: 60 },
    { module: "pdf-report", module_name: "Rapport", runs: 1, files: 1, minutes_saved: 5 },
  ],
});

describe("usage stats", () => {
  it("parses the engine counters and sums them", () => {
    const stats = parseUsageStats(RAW);
    expect(stats.features).toHaveLength(2);
    expect(totalsOf(stats)).toMatchObject({ runs: 4, files: 13, minutes_saved: 65 });
    expect(() => parseUsageStats("{}")).toThrow("invalides");
  });

  it("formats saved time in working days", () => {
    expect(formatSavedTime(45)).toBe("45 min");
    expect(formatSavedTime(125)).toBe("2 h");
    expect(formatSavedTime(8 * 60)).toBe("1 jour");
    expect(formatSavedTime(19 * 60)).toBe("2 jours 3 h");
  });
});

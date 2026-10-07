import { describe, expect, it } from "vitest";
import {
  CONSOLE_CAPACITY,
  clampDockHeight,
  DEFAULT_FILTER,
  describeOs,
  EMPTY_SELECTION,
  filterEntries,
  formatEntry,
  formatForSupport,
  formatTime,
  isScrolledToBottom,
  mergeEntries,
  recentErrors,
  selectAll,
  selectEntry,
  selectedEntries,
  toLevelFilter,
  toSourceFilter,
  unseenErrorCount,
  type ConsoleEntry,
} from "./console";

const NOON = new Date(2026, 9, 7, 12, 3, 4, 5).getTime();

function entry(id: number, overrides: Partial<ConsoleEntry> = {}): ConsoleEntry {
  return {
    id,
    timestamp: NOON,
    level: "info",
    source: "app",
    message: `m${String(id)}`,
    ...overrides,
  };
}

describe("filterEntries", () => {
  const entries = [
    entry(1, { level: "debug" }),
    entry(2, { level: "info", source: "engine", module: "dwg-parts" }),
    entry(3, { level: "warning", detail: "C:\\Plans\\Façade.dwg" }),
    entry(4, { level: "error", source: "bridge", message: "Moteur introuvable" }),
  ];
  const ids = (filtered: ConsoleEntry[]) => filtered.map(({ id }) => id);

  it("keeps everything by default", () => {
    expect(ids(filterEntries(entries, DEFAULT_FILTER))).toEqual([1, 2, 3, 4]);
  });

  it("filters by minimum level", () => {
    expect(ids(filterEntries(entries, { ...DEFAULT_FILTER, level: "warnings" }))).toEqual([3, 4]);
    expect(ids(filterEntries(entries, { ...DEFAULT_FILTER, level: "errors" }))).toEqual([4]);
  });

  it("filters by source", () => {
    expect(ids(filterEntries(entries, { ...DEFAULT_FILTER, source: "engine" }))).toEqual([2]);
  });

  it("searches message, detail and module without case", () => {
    const search = (query: string) => ids(filterEntries(entries, { ...DEFAULT_FILTER, query }));
    expect(search("INTROUVABLE")).toEqual([4]);
    expect(search("façade")).toEqual([3]);
    expect(search("dwg-parts")).toEqual([2]);
    expect(search("   ")).toEqual([1, 2, 3, 4]);
  });

  it("falls back to showing everything for unknown filter values", () => {
    expect(toLevelFilter("errors")).toBe("errors");
    expect(toLevelFilter("nope")).toBe("all");
    expect(toSourceFilter("rust")).toBe("rust");
    expect(toSourceFilter("nope")).toBe("all");
  });
});

describe("mergeEntries", () => {
  it("appends newer entries in order", () => {
    const merged = mergeEntries([entry(1), entry(2)], [entry(3)]);
    expect(merged.map(({ id }) => id)).toEqual([1, 2, 3]);
  });

  it("deduplicates entries received both by event and by the initial load", () => {
    const merged = mergeEntries([entry(5)], [entry(3), entry(4), entry(5)]);
    expect(merged.map(({ id }) => id)).toEqual([3, 4, 5]);
  });

  it("keeps only the buffer's capacity", () => {
    const many = Array.from({ length: CONSOLE_CAPACITY + 2 }, (_, index) => entry(index));
    const merged = mergeEntries([], many);
    expect(merged).toHaveLength(CONSOLE_CAPACITY);
    expect(merged[0]?.id).toBe(2);
  });
});

describe("badge and recent errors", () => {
  const entries = [
    entry(1, { level: "error" }),
    entry(2, { level: "warning" }),
    entry(3, { level: "error" }),
    entry(4, { level: "error" }),
  ];

  it("counts only errors newer than the last seen entry", () => {
    expect(unseenErrorCount(entries, -1)).toBe(3);
    expect(unseenErrorCount(entries, 3)).toBe(1);
    expect(unseenErrorCount(entries, 4)).toBe(0);
  });

  it("returns the latest errors, oldest first", () => {
    expect(recentErrors(entries, 2).map(({ id }) => id)).toEqual([3, 4]);
  });
});

describe("selection", () => {
  const visible = [10, 11, 12, 13, 14];

  it("selects a single line on a plain click", () => {
    const selection = selectEntry(selectAll(visible), 12, visible, "single");
    expect([...selection.ids]).toEqual([12]);
    expect(selection.anchor).toBe(12);
  });

  it("adds and removes lines with Ctrl+click", () => {
    const first = selectEntry(EMPTY_SELECTION, 10, visible, "toggle");
    const both = selectEntry(first, 13, visible, "toggle");
    expect([...both.ids].sort()).toEqual([10, 13]);
    expect([...selectEntry(both, 10, visible, "toggle").ids]).toEqual([13]);
  });

  it("selects a range from the anchor with Shift+click, in both directions", () => {
    const anchored = selectEntry(EMPTY_SELECTION, 13, visible, "single");
    expect([...selectEntry(anchored, 11, visible, "range").ids]).toEqual([11, 12, 13]);
    const extended = selectEntry(anchored, 14, visible, "range");
    expect([...extended.ids]).toEqual([13, 14]);
    expect(extended.anchor).toBe(13);
  });

  it("treats a range without a visible anchor as a single click", () => {
    expect([...selectEntry(EMPTY_SELECTION, 12, visible, "range").ids]).toEqual([12]);
  });

  it("returns selected entries in log order", () => {
    const entries = [entry(1), entry(2), entry(3)];
    const selection = { ids: new Set([3, 1]), anchor: 3 };
    expect(selectedEntries(entries, selection).map(({ id }) => id)).toEqual([1, 3]);
  });
});

describe("support format", () => {
  it("formats the local time with milliseconds", () => {
    expect(formatTime(NOON)).toBe("12:03:04.005");
  });

  it("writes level, origin and message on one line, detail indented below", () => {
    const formatted = formatEntry(
      entry(1, {
        level: "error",
        source: "engine",
        module: "dwg-parts",
        message: "Plan illisible",
        detail: "C:\\Plans\\A.dwg\r\nRéexportez-le",
      }),
    );
    expect(formatted).toBe(
      "[12:03:04.005] ERROR [engine/dwg-parts] Plan illisible\n" +
        "    C:\\Plans\\A.dwg\n" +
        "    Réexportez-le",
    );
    expect(formatEntry(entry(2))).toBe("[12:03:04.005] INFO [app] m2");
  });

  it("starts with the version, the system and the ISO date", () => {
    const date = new Date(Date.UTC(2026, 9, 7, 10, 0, 0));
    const text = formatForSupport([entry(1)], { version: "0.20.0", os: "Windows NT 10.0", date });
    expect(text.split("\n")).toEqual([
      "Drawflow v0.20.0 · Windows NT 10.0 · 2026-10-07T10:00:00.000Z",
      "[12:03:04.005] INFO [app] m1",
    ]);
  });

  it("summarises the user agent", () => {
    expect(
      describeOs("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0"),
    ).toBe("Windows NT 10.0 x64");
    expect(describeOs("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit")).toBe("macOS");
    expect(describeOs("Mozilla/5.0 (X11; Linux x86_64)")).toBe("Linux");
    expect(describeOs("")).toBe("OS ?");
  });
});

describe("panel layout", () => {
  it("follows new entries only when already at the bottom", () => {
    expect(isScrolledToBottom(1000, 600, 400)).toBe(true);
    expect(isScrolledToBottom(1000, 590, 400)).toBe(true);
    expect(isScrolledToBottom(1000, 300, 400)).toBe(false);
  });

  it("keeps the docked panel within usable bounds", () => {
    expect(clampDockHeight(50, 800)).toBe(140);
    expect(clampDockHeight(300, 800)).toBe(300);
    expect(clampDockHeight(2000, 800)).toBe(600);
    expect(clampDockHeight(300, 100)).toBe(140);
  });
});

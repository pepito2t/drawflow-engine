import { z } from "zod";

export const CONSOLE_LEVELS = ["debug", "info", "warning", "error"] as const;
export const CONSOLE_SOURCES = ["engine", "app", "bridge", "assistant", "setup", "rust"] as const;
/** Same capacity as the bridge's ring buffer (`CONSOLE_CAPACITY` in console.rs). */
export const CONSOLE_CAPACITY = 5000;
/** Rendering thousands of rows would slow the window down; copying still covers everything. */
export const CONSOLE_DISPLAY_LIMIT = 500;
export const RECENT_ERRORS_LIMIT = 50;

export const consoleEntrySchema = z.object({
  id: z.number().int().nonnegative(),
  timestamp: z.number().nonnegative(),
  level: z.enum(CONSOLE_LEVELS),
  source: z.enum(CONSOLE_SOURCES),
  module: z.string().optional(),
  message: z.string(),
  detail: z.string().optional(),
});

export type ConsoleEntry = z.infer<typeof consoleEntrySchema>;
export type ConsoleLevel = ConsoleEntry["level"];
export type ConsoleSource = ConsoleEntry["source"];

/** What a capture point reports; the bridge assigns id and time, then masks secrets. */
export interface ConsoleDraft {
  level: ConsoleLevel;
  source: ConsoleSource;
  module?: string;
  message: string;
  detail?: string;
}

export const LEVEL_FILTERS = ["all", "warnings", "errors"] as const;
export type LevelFilter = (typeof LEVEL_FILTERS)[number];
export type SourceFilter = "all" | ConsoleSource;

export function toLevelFilter(value: string): LevelFilter {
  return LEVEL_FILTERS.find((filter) => filter === value) ?? "all";
}

export function toSourceFilter(value: string): SourceFilter {
  return CONSOLE_SOURCES.find((source) => source === value) ?? "all";
}

export interface ConsoleFilter {
  level: LevelFilter;
  source: SourceFilter;
  query: string;
}

export const DEFAULT_FILTER: ConsoleFilter = { level: "all", source: "all", query: "" };

const LEVEL_RANK: Record<ConsoleLevel, number> = { debug: 0, info: 1, warning: 2, error: 3 };
const MINIMUM_RANK: Record<LevelFilter, number> = { all: 0, warnings: 2, errors: 3 };

export function matchesFilter(entry: ConsoleEntry, filter: ConsoleFilter): boolean {
  if (LEVEL_RANK[entry.level] < MINIMUM_RANK[filter.level]) {
    return false;
  }
  if (filter.source !== "all" && entry.source !== filter.source) {
    return false;
  }
  const query = filter.query.trim().toLowerCase();
  if (!query) {
    return true;
  }
  return [entry.message, entry.detail, entry.module, entry.source].some((text) =>
    text?.toLowerCase().includes(query),
  );
}

export function filterEntries(
  entries: readonly ConsoleEntry[],
  filter: ConsoleFilter,
): ConsoleEntry[] {
  return entries.filter((entry) => matchesFilter(entry, filter));
}

/** Keeps id order and the buffer's capacity; entries already known are ignored. */
export function mergeEntries(
  current: readonly ConsoleEntry[],
  incoming: readonly ConsoleEntry[],
): ConsoleEntry[] {
  if (followsInOrder(lastEntryId(current), incoming)) {
    return [...current, ...incoming].slice(-CONSOLE_CAPACITY);
  }
  const byId = new Map(current.map((entry) => [entry.id, entry]));
  for (const entry of incoming) {
    byId.set(entry.id, entry);
  }
  return [...byId.values()].sort((left, right) => left.id - right.id).slice(-CONSOLE_CAPACITY);
}

function followsInOrder(lastId: number, incoming: readonly ConsoleEntry[]): boolean {
  let previous = lastId;
  for (const entry of incoming) {
    if (entry.id <= previous) {
      return false;
    }
    previous = entry.id;
  }
  return true;
}

export function unseenErrorCount(entries: readonly ConsoleEntry[], lastSeenId: number): number {
  return entries.filter((entry) => entry.level === "error" && entry.id > lastSeenId).length;
}

export function lastEntryId(entries: readonly ConsoleEntry[]): number {
  return entries.at(-1)?.id ?? -1;
}

export function recentErrors(
  entries: readonly ConsoleEntry[],
  limit = RECENT_ERRORS_LIMIT,
): ConsoleEntry[] {
  return entries.filter((entry) => entry.level === "error").slice(-limit);
}

export interface Selection {
  ids: ReadonlySet<number>;
  anchor: number | null;
}

export type SelectionMode = "single" | "toggle" | "range";

export const EMPTY_SELECTION: Selection = { ids: new Set(), anchor: null };

/** Same rules as a file explorer: click, Ctrl+click to add or remove, Shift+click for a range. */
export function selectEntry(
  selection: Selection,
  clickedId: number,
  visibleIds: readonly number[],
  mode: SelectionMode,
): Selection {
  if (mode === "toggle") {
    const ids = new Set(selection.ids);
    if (ids.has(clickedId)) {
      ids.delete(clickedId);
    } else {
      ids.add(clickedId);
    }
    return { ids, anchor: clickedId };
  }
  const anchorIndex = selection.anchor === null ? -1 : visibleIds.indexOf(selection.anchor);
  const clickedIndex = visibleIds.indexOf(clickedId);
  if (mode === "single" || anchorIndex === -1 || clickedIndex === -1) {
    return { ids: new Set([clickedId]), anchor: clickedId };
  }
  const [from, to] = [Math.min(anchorIndex, clickedIndex), Math.max(anchorIndex, clickedIndex)];
  return { ids: new Set(visibleIds.slice(from, to + 1)), anchor: selection.anchor };
}

export function selectAll(visibleIds: readonly number[]): Selection {
  return { ids: new Set(visibleIds), anchor: visibleIds[0] ?? null };
}

export function selectedEntries(
  entries: readonly ConsoleEntry[],
  selection: Selection,
): ConsoleEntry[] {
  return entries.filter((entry) => selection.ids.has(entry.id));
}

/** A few pixels of slack: fractional scrolling on scaled Windows displays never reaches 0. */
const BOTTOM_TOLERANCE_PX = 24;

export function isScrolledToBottom(
  scrollHeight: number,
  scrollTop: number,
  clientHeight: number,
): boolean {
  return scrollHeight - scrollTop - clientHeight <= BOTTOM_TOLERANCE_PX;
}

export const DEFAULT_DOCK_HEIGHT = 280;
const MIN_DOCK_HEIGHT = 140;
const MAX_DOCK_SHARE = 0.75;

export function clampDockHeight(height: number, viewportHeight: number): number {
  const maximum = Math.max(MIN_DOCK_HEIGHT, Math.round(viewportHeight * MAX_DOCK_SHARE));
  return Math.min(maximum, Math.max(MIN_DOCK_HEIGHT, Math.round(height)));
}

export interface SupportHeader {
  version: string;
  os: string;
  date: Date;
}

const DETAIL_INDENT = "    ";
const TIME_PAD = 2;
const MILLISECONDS_PAD = 3;

export function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  const pad = (value: number, length = TIME_PAD) => String(value).padStart(length, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), MILLISECONDS_PAD)}`;
}

export function entryOrigin(entry: ConsoleEntry): string {
  return entry.module ? `${entry.source}/${entry.module}` : entry.source;
}

/** Fixed English level names: the support reads the same words whatever the app language. */
export function formatEntry(entry: ConsoleEntry): string {
  const line = `[${formatTime(entry.timestamp)}] ${entry.level.toUpperCase()} [${entryOrigin(entry)}] ${entry.message}`;
  if (!entry.detail) {
    return line;
  }
  const detail = entry.detail
    .split(/\r?\n/)
    .map((detailLine) => DETAIL_INDENT + detailLine)
    .join("\n");
  return `${line}\n${detail}`;
}

export function formatSupportHeader({ version, os, date }: SupportHeader): string {
  return `Drawflow v${version} · ${os} · ${date.toISOString()}`;
}

export function formatForSupport(entries: readonly ConsoleEntry[], header: SupportHeader): string {
  return [formatSupportHeader(header), ...entries.map(formatEntry)].join("\n");
}

const UNKNOWN_OS = "OS ?";

/** Summarises the webview's user agent: no extra permission is needed to know the system. */
export function describeOs(userAgent: string): string {
  const windows = /Windows NT ([\d.]+)/.exec(userAgent);
  if (windows) {
    const architecture = /arm64|aarch64/i.test(userAgent)
      ? " ARM64"
      : /Win64|x64|WOW64/.test(userAgent)
        ? " x64"
        : "";
    return `Windows NT ${windows[1] ?? ""}${architecture}`;
  }
  if (/Mac OS X|Macintosh/.test(userAgent)) {
    return "macOS";
  }
  if (/Linux/.test(userAgent)) {
    return "Linux";
  }
  return UNKNOWN_OS;
}

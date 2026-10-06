import { z } from "zod";
import { CatalogError } from "./catalog";
import { parseJsonOrNull } from "./json";

const historyEntrySchema = z.object({
  id: z.string(),
  started_at: z.string(),
  module: z.string(),
  module_name: z.string(),
  inputs: z.record(z.string(), z.unknown()),
  status: z.enum(["succeeded", "failed"]),
  summary: z.string(),
  outputs: z.array(z.string()),
  warnings: z.array(z.string()),
  error: z.string().nullable(),
  duration_ms: z.number(),
});

const historyResponseSchema = z.object({ entries: z.array(historyEntrySchema) });

export type HistoryEntry = z.infer<typeof historyEntrySchema>;

const SECOND_MS = 1000;
const MINUTE_MS = 60 * SECOND_MS;
const SAME_DAY_FORMAT: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit" };
const OTHER_DAY_FORMAT: Intl.DateTimeFormatOptions = {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
};

export function parseHistory(rawJson: string): HistoryEntry[] {
  const parsed = historyResponseSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError("L'historique reçu du moteur est invalide.");
  }
  return parsed.data.entries;
}

export function describeDuration(durationMs: number): string {
  if (durationMs < SECOND_MS) {
    return "< 1 s";
  }
  if (durationMs < MINUTE_MS) {
    return `${String(Math.round(durationMs / SECOND_MS))} s`;
  }
  const minutes = Math.floor(durationMs / MINUTE_MS);
  const seconds = Math.round((durationMs - minutes * MINUTE_MS) / SECOND_MS);
  return `${String(minutes)} min ${String(seconds).padStart(2, "0")} s`;
}

/** Time only for today's runs, date and time otherwise. */
export function describeStart(startedAt: string, now: Date = new Date()): string {
  const started = new Date(startedAt);
  if (Number.isNaN(started.getTime())) {
    return startedAt;
  }
  const sameDay = started.toDateString() === now.toDateString();
  return started.toLocaleString("fr-CH", sameDay ? SAME_DAY_FORMAT : OTHER_DAY_FORMAT);
}

export function lastOutput(entry: HistoryEntry): string | null {
  return entry.outputs.at(-1) ?? null;
}

import { t } from "../i18n/shell";
import { z } from "zod";
import { parseJsonOrNull } from "./json";

const progressEventSchema = z.object({
  type: z.literal("progress"),
  current: z.number().int().nonnegative(),
  total: z.number().int().positive(),
  message: z.string(),
});

const logEventSchema = z.object({ type: z.literal("log"), message: z.string() });

const warningEventSchema = z.object({
  type: z.literal("warning"),
  message: z.string(),
  file: z.string().nullable(),
  location: z.string().nullable().optional(),
  hint: z.string().nullable().optional(),
});

const tableRowSchema = z.object({ cells: z.array(z.string()), issues: z.array(z.string()) });

const tableEventSchema = z.object({
  type: z.literal("table"),
  headers: z.array(z.string()),
  rows: z.array(tableRowSchema),
  total: z.number(),
});

const resultEventSchema = z.object({
  type: z.literal("result"),
  summary: z.string(),
  outputs: z.array(z.string()),
});

export const errorEventSchema = z.object({
  type: z.literal("error"),
  message: z.string(),
  file: z.string().nullable(),
  hint: z.string().nullable(),
});

export const engineEventSchema = z.discriminatedUnion("type", [
  progressEventSchema,
  logEventSchema,
  warningEventSchema,
  tableEventSchema,
  resultEventSchema,
  errorEventSchema,
]);

export type EngineEvent = z.infer<typeof engineEventSchema>;
export type ProgressEvent = z.infer<typeof progressEventSchema>;
export type TableEvent = z.infer<typeof tableEventSchema>;
export type TableRow = z.infer<typeof tableRowSchema>;

export function unreadableEventMessage(): string {
  return t("events.unreadable");
}

export function parseEventLine(line: string): EngineEvent {
  const parsed = engineEventSchema.safeParse(parseJsonOrNull(line));
  if (parsed.success) {
    return parsed.data;
  }
  return { type: "error", message: unreadableEventMessage(), file: null, hint: line };
}

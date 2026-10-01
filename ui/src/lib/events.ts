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
});

const resultEventSchema = z.object({
  type: z.literal("result"),
  summary: z.string(),
  outputs: z.array(z.string()),
});

const errorEventSchema = z.object({
  type: z.literal("error"),
  message: z.string(),
  file: z.string().nullable(),
  hint: z.string().nullable(),
});

export const engineEventSchema = z.discriminatedUnion("type", [
  progressEventSchema,
  logEventSchema,
  warningEventSchema,
  resultEventSchema,
  errorEventSchema,
]);

export type EngineEvent = z.infer<typeof engineEventSchema>;
export type ProgressEvent = z.infer<typeof progressEventSchema>;

export const UNREADABLE_EVENT_MESSAGE = "Message illisible reçu du moteur.";

export function parseEventLine(line: string): EngineEvent {
  const parsed = engineEventSchema.safeParse(parseJsonOrNull(line));
  if (parsed.success) {
    return parsed.data;
  }
  return { type: "error", message: UNREADABLE_EVENT_MESSAGE, file: null, hint: line };
}

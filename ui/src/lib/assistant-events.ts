import { z } from "zod";
import { errorEventSchema, UNREADABLE_EVENT_MESSAGE } from "./events";
import { parseJsonOrNull } from "./json";

export const assistantEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("delta"), text: z.string() }),
  z.object({
    type: z.literal("tool_call"),
    id: z.string(),
    name: z.string(),
    arguments: z.record(z.string(), z.unknown()),
  }),
  z.object({ type: z.literal("tool_result"), id: z.string(), name: z.string(), ok: z.boolean() }),
  z.object({ type: z.literal("done") }),
  errorEventSchema,
]);

export type AssistantEvent = z.infer<typeof assistantEventSchema>;

export function parseAssistantLine(line: string): AssistantEvent {
  const parsed = assistantEventSchema.safeParse(parseJsonOrNull(line));
  if (parsed.success) {
    return parsed.data;
  }
  return { type: "error", message: UNREADABLE_EVENT_MESSAGE, file: null, hint: line };
}

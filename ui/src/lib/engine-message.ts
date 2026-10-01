import { z } from "zod";

export const engineMessageSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("stdout"), line: z.string() }),
  z.object({ kind: z.literal("stderr"), line: z.string() }),
  z.object({ kind: z.literal("exit"), code: z.number().int().nullable() }),
]);

export type EngineMessage = z.infer<typeof engineMessageSchema>;

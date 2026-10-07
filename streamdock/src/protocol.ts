import * as z from "zod/mini";

export const PROTOCOL_VERSION = 1;

const runStatusSchema = z.enum(["idle", "running", "succeeded", "failed", "cancelled"]);

export const appStateSchema = z.object({
  modules: z.array(z.object({ id: z.string(), name: z.string(), icon: z.string() })),
  presets: z.array(z.object({ id: z.string(), name: z.string(), module: z.string() })),
  runs: z.array(
    z.object({
      moduleId: z.string(),
      status: runStatusSchema,
      current: z.nullable(z.number()),
      total: z.nullable(z.number()),
    }),
  ),
});

export const appEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("runStarted"), moduleId: z.string() }),
  z.object({
    type: z.literal("runProgress"),
    moduleId: z.string(),
    current: z.number(),
    total: z.number(),
  }),
  z.object({
    type: z.literal("runFinished"),
    moduleId: z.string(),
    outcome: z.enum(["succeeded", "failed", "cancelled"]),
  }),
  z.object({ type: z.literal("presetSaved") }),
  z.object({ type: z.literal("resync") }),
]);

export const serverMessageSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("welcome"), version: z.number(), locked: z.boolean() }),
  z.object({ type: z.literal("locked"), locked: z.boolean() }),
  z.object({ type: z.literal("error"), message: z.string() }),
  z.object({
    type: z.literal("result"),
    id: z.string(),
    ok: z.boolean(),
    error: z.optional(z.string()),
    data: z.optional(z.unknown()),
  }),
  z.object({ type: z.literal("event"), event: z.unknown() }),
]);

export type AppState = z.infer<typeof appStateSchema>;
export type AppEvent = z.infer<typeof appEventSchema>;
export type ServerMessage = z.infer<typeof serverMessageSchema>;
export type RunStatus = z.infer<typeof runStatusSchema>;
export type CommandResult = { ok: true; data?: unknown } | { ok: false; error: string };

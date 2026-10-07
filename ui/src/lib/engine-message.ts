import { z } from "zod";
import { t } from "../i18n/shell";

export const engineMessageSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("stdout"), line: z.string() }),
  z.object({ kind: z.literal("stderr"), line: z.string() }),
  z.object({ kind: z.literal("exit"), code: z.number().int().nullable() }),
]);

export type EngineMessage = z.infer<typeof engineMessageSchema>;

export const SUCCESS_EXIT_CODE = 0;

export type EngineMessageHandler = (message: EngineMessage) => void;
export type InvalidMessageHandler = (message: string) => void;

/** Validates each raw bridge message; a throw inside a channel callback would be lost. */
export function channelListener(
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): (raw: unknown) => void {
  return (raw) => {
    const parsed = engineMessageSchema.safeParse(raw);
    if (parsed.success) {
      onMessage(parsed.data);
    } else {
      onInvalid(t("engineChannel.invalidMessage"));
    }
  };
}

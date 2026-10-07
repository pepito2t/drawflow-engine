import { z } from "zod";
import { t } from "../../i18n/shell";

export const bridgeErrorSchema = z.object({
  code: z.string(),
  params: z.record(z.string(), z.union([z.string(), z.number()])).catch({}),
  message: z.string(),
});

export type BridgeError = z.infer<typeof bridgeErrorSchema>;

export function parseBridgeError(value: unknown): BridgeError | null {
  const parsed = bridgeErrorSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}

/** Unknown codes come from a newer Rust bridge: its English message beats a generic text. */
export function translateBridgeError({ code, params, message }: BridgeError): string {
  const key = `bridge.${code}`;
  if (t.has(key)) {
    return t(key, params);
  }
  return message || t("bridge.unknownError");
}

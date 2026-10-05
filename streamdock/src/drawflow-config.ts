import { z } from "zod";
import type { Connection } from "./drawflow-client";

/** Drawflow's own local API settings; reading them spares the user any port or token entry. */
const DRAWFLOW_CONFIG_PARTS = ["ch.drawflow.desktop", "integrations.json"] as const;

const configSchema = z.object({
  enabled: z.boolean(),
  port: z.number().int().positive(),
  token: z.string(),
});

export type ReadFile = (path: string) => string | null;

export function drawflowConfigPath(env: NodeJS.ProcessEnv, separator: string): string | null {
  const appData = env.APPDATA;
  if (!appData) {
    return null;
  }
  return [appData, ...DRAWFLOW_CONFIG_PARTS].join(separator);
}

/** Null when the API is disabled or the file is absent or unreadable: the key settings apply. */
export function parseDrawflowConfig(text: string): Connection | null {
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    return null;
  }
  const parsed = configSchema.safeParse(raw);
  if (!parsed.success || !parsed.data.enabled || !parsed.data.token) {
    return null;
  }
  return { port: parsed.data.port, token: parsed.data.token };
}

export function loadDrawflowConnection(
  readFile: ReadFile,
  env: NodeJS.ProcessEnv,
  separator: string,
): Connection | null {
  const path = drawflowConfigPath(env, separator);
  if (path === null) {
    return null;
  }
  const text = readFile(path);
  return text === null ? null : parseDrawflowConfig(text);
}

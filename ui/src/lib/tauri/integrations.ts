import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { z } from "zod";
import { bridgeErrorSchema } from "./bridge-error";

const COMMAND_EVENT = "integration-command";

const statusSchema = z.object({
  enabled: z.boolean(),
  port: z.number().int(),
  token: z.string(),
  address: z.string().nullable(),
  error: bridgeErrorSchema.nullable(),
});

const commandRequestSchema = z.object({ id: z.string(), command: z.string(), args: z.unknown() });

export type IntegrationStatus = z.infer<typeof statusSchema>;
export type IntegrationCommand = z.infer<typeof commandRequestSchema>;

export interface IntegrationReply {
  id: string;
  ok: boolean;
  error?: string;
  data?: unknown;
}

export async function getIntegrationStatus(): Promise<IntegrationStatus> {
  return statusSchema.parse(await invoke("integration_status"));
}

export function updateIntegration(
  enabled: boolean,
  port: number,
  regenerateToken: boolean,
): Promise<void> {
  return invoke<undefined>("integration_update", { enabled, port, regenerateToken });
}

export function listenToIntegrationCommands(
  onCommand: (command: IntegrationCommand) => void,
): Promise<() => void> {
  return listen<unknown>(COMMAND_EVENT, ({ payload }) => {
    onCommand(commandRequestSchema.parse(payload));
  });
}

export function replyToIntegration(reply: IntegrationReply): Promise<void> {
  return invoke<undefined>("integration_reply", { reply });
}

export function publishToIntegrations(event: unknown): Promise<void> {
  return invoke<undefined>("integration_publish", { event });
}

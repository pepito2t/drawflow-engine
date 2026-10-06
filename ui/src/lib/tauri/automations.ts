import { invoke } from "@tauri-apps/api/core";
import { z } from "zod";

const automationSchema = z.object({
  id: z.string().min(1),
  folder: z.string(),
  presetId: z.string(),
  enabled: z.boolean(),
});

const statusSchema = z.object({
  automations: z.array(automationSchema),
  errors: z.array(z.string()),
});

export type Automation = z.infer<typeof automationSchema>;
export type AutomationStatus = z.infer<typeof statusSchema>;

export async function getAutomationStatus(): Promise<AutomationStatus> {
  return statusSchema.parse(await invoke("automation_status"));
}

export async function saveAutomations(automations: Automation[]): Promise<AutomationStatus> {
  return statusSchema.parse(await invoke("automation_save", { automations }));
}

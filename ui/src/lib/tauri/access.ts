import { invoke } from "./invoke";
import { z } from "zod";

const lockStatusSchema = z.object({ required: z.boolean(), unlocked: z.boolean() });

export type LockStatus = z.infer<typeof lockStatusSchema>;

export async function getLockStatus(): Promise<LockStatus> {
  return lockStatusSchema.parse(await invoke("lock_status"));
}

export function unlock(code: string): Promise<void> {
  return invoke<undefined>("unlock", { code });
}

export function changeAccessCode(current: string, newCode: string): Promise<void> {
  return invoke<undefined>("change_access_code", { current, newCode });
}

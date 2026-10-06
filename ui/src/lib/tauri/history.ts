import { parseHistory, type HistoryEntry } from "../history";
import { parseUsageStats, type UsageStats } from "../stats";
import { engineRequest } from "./engine";

export async function listHistory(): Promise<HistoryEntry[]> {
  return parseHistory(await engineRequest("history.list"));
}

export async function removeHistoryEntry(id: string): Promise<void> {
  await engineRequest("history.remove", { id });
}

export async function clearHistory(): Promise<void> {
  await engineRequest("history.clear");
}

export async function getUsageStats(): Promise<UsageStats> {
  return parseUsageStats(await engineRequest("history.stats"));
}

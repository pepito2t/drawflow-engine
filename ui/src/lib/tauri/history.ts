import { parseHistory, type HistoryEntry } from "../history";
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

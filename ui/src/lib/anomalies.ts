import { t } from "../i18n/shell";
import { fileName } from "./paths";
import type { LogEntry } from "./run-state";

export interface AnomalyGroup {
  file: string | null;
  fileName: string;
  items: LogEntry[];
}

export function anomaliesOf(log: LogEntry[]): LogEntry[] {
  return log.filter((entry) => entry.level === "warning");
}

/** One group per file, in order of first appearance; file-less anomalies come first. */
export function groupAnomalies(log: LogEntry[]): AnomalyGroup[] {
  const groups = new Map<string | null, LogEntry[]>();
  for (const entry of anomaliesOf(log)) {
    const items = groups.get(entry.file) ?? [];
    items.push(entry);
    groups.set(entry.file, items);
  }
  return [...groups.entries()]
    .map(([file, items]) => ({
      file,
      fileName: file === null ? t("anomalies.general") : fileName(file),
      items,
    }))
    .sort((left, right) => Number(left.file !== null) - Number(right.file !== null));
}

/** Plain text to paste in an e-mail or a ticket. */
export function anomaliesAsText(groups: AnomalyGroup[]): string {
  return groups
    .map((group) => {
      const lines = group.items.map((item) => {
        const where = item.location ? ` (${item.location})` : "";
        const hint = item.hint ? ` → ${item.hint}` : "";
        return `- ${item.message}${where}${hint}`;
      });
      return [group.file ?? t("anomalies.general"), ...lines].join("\n");
    })
    .join("\n\n");
}

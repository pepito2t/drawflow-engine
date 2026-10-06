import { t } from "../i18n/shell";
import type { RunStatus } from "./run-state";

export function statusLabel(status: RunStatus): string {
  return t(`runStatus.${status}`);
}

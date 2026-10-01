import type { RunStatus } from "./run-state";

export const STATUS_LABELS: Record<RunStatus, string> = {
  idle: "Prêt",
  running: "En cours",
  succeeded: "Terminé",
  failed: "Échec",
  cancelled: "Annulé",
};

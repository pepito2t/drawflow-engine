import { useState } from "react";
import { useRunsStore } from "../hooks/runs-context";
import type { CatalogModule } from "../lib/catalog";
import { STATUS_LABELS } from "../lib/run-labels";
import { entryFor, overallProgress, runningModuleIds, visibleRunIds } from "../lib/runs-store";
import { ActivityIcon } from "./icons";

interface RunsIndicatorProps {
  modules: CatalogModule[];
  onOpenModule: (moduleId: string) => void;
}

const PERCENT = 100;

export function RunsIndicator({ modules, onOpenModule }: RunsIndicatorProps) {
  const { state } = useRunsStore();
  const [isOpen, setIsOpen] = useState(false);
  const running = runningModuleIds(state).length;
  const progress = overallProgress(state);
  const listed = visibleRunIds(state);

  return (
    <div className="runs-indicator">
      <button
        type="button"
        className={running > 0 ? "icon-button active" : "icon-button"}
        aria-expanded={isOpen}
        aria-label="Traitements"
        title={describeRunning(running, progress)}
        onClick={() => {
          setIsOpen((open) => !open);
        }}
      >
        <ActivityIcon />
        {running > 0 && <span className="icon-badge">{running}</span>}
      </button>
      {isOpen && (
        <div className="runs-popover" role="dialog" aria-label="Traitements">
          <strong className="popover-title">{describeRunning(running, progress)}</strong>
          {listed.length === 0 && <p className="muted">Aucun traitement lancé.</p>}
          {listed.map((moduleId) => {
            const { run } = entryFor(state, moduleId);
            const name = modules.find((module) => module.manifest.id === moduleId)?.manifest.name;
            return (
              <button
                key={moduleId}
                type="button"
                className="runs-item"
                onClick={() => {
                  onOpenModule(moduleId);
                  setIsOpen(false);
                }}
              >
                <span className="runs-item-header">
                  <span>{name ?? moduleId}</span>
                  <span className={`run-status ${run.status}`}>{STATUS_LABELS[run.status]}</span>
                </span>
                {run.status === "running" && (
                  <progress value={run.progress?.current} max={run.progress?.total ?? 1} />
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function describeRunning(count: number, progress: number | null): string {
  if (count === 0) {
    return "Aucun traitement en cours";
  }
  const label = count === 1 ? "1 traitement en cours" : `${String(count)} traitements en cours`;
  return progress === null ? label : `${label} · ${String(Math.round(progress * PERCENT))} %`;
}

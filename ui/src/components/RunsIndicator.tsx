import { plural } from "../i18n";
import { t } from "../i18n/shell";
import { useCallback, useRef, useState } from "react";
import { useRunsSelector, useRunsState } from "../hooks/runs-context";
import { useDismiss } from "../hooks/use-dismiss";
import type { CatalogModule } from "../lib/catalog";
import { statusLabel } from "../lib/run-labels";
import { entryFor, overallProgress, runningModuleIds, visibleRunIds } from "../lib/runs-store";
import { ActivityIcon } from "./icons";

interface RunsIndicatorProps {
  modules: CatalogModule[];
  onOpenModule: (moduleId: string) => void;
}

const PERCENT = 100;

export function RunsIndicator({ modules, onOpenModule }: RunsIndicatorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const close = useCallback(() => {
    setIsOpen(false);
  }, []);
  useDismiss(container, isOpen, close);
  const running = useRunsSelector((state) => runningModuleIds(state).length);
  const progress = useRunsSelector(overallProgress);

  return (
    <div className="runs-indicator" ref={container}>
      <button
        type="button"
        className={running > 0 ? "icon-button active" : "icon-button"}
        aria-expanded={isOpen}
        aria-label={t("runsIndicator.title")}
        title={describeRunning(running, progress)}
        onClick={() => {
          setIsOpen((open) => !open);
        }}
      >
        <ActivityIcon />
        {running > 0 && <span className="icon-badge">{running}</span>}
      </button>
      {isOpen && (
        <RunsPopover
          modules={modules}
          title={describeRunning(running, progress)}
          onOpenModule={(moduleId) => {
            onOpenModule(moduleId);
            close();
          }}
        />
      )}
    </div>
  );
}

interface RunsPopoverProps {
  modules: CatalogModule[];
  title: string;
  onOpenModule: (moduleId: string) => void;
}

/** Follows every run's progress, so it only exists while open. */
function RunsPopover({ modules, title, onOpenModule }: RunsPopoverProps) {
  const state = useRunsState();
  const listed = visibleRunIds(state);
  return (
    <div className="runs-popover" role="dialog" aria-label={t("runsIndicator.title")}>
      <strong className="popover-title">{title}</strong>
      {listed.length === 0 && <p className="muted">{t("runsIndicator.empty")}</p>}
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
            }}
          >
            <span className="runs-item-header">
              <span>{name ?? moduleId}</span>
              <span className={`run-status ${run.status}`}>{statusLabel(run.status)}</span>
            </span>
            {run.status === "running" && (
              <progress value={run.progress?.current} max={run.progress?.total ?? 1} />
            )}
          </button>
        );
      })}
    </div>
  );
}

function describeRunning(count: number, progress: number | null): string {
  if (count === 0) {
    return t("runsIndicator.none");
  }
  const label = plural(count, t("runsIndicator.running.one"), t("runsIndicator.running.other"));
  return progress === null
    ? label
    : t("runsIndicator.progress", { label, percent: Math.round(progress * PERCENT) });
}

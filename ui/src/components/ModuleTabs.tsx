import type { ReactNode } from "react";
import { useRunsStore } from "../hooks/runs-context";
import type { CatalogModule } from "../lib/catalog";
import { entryFor } from "../lib/runs-store";
import type { RunStatus } from "../lib/run-state";
import { ModuleIconView } from "./ModuleIconView";
import { Spinner } from "./Spinner";

interface ModuleTabsProps {
  modules: CatalogModule[];
  selectedId: string | null;
  onSelect: (moduleId: string) => void;
  footer: ReactNode;
}

export const tabPanelId = (moduleId: string) => `panel-${moduleId}`;

export function ModuleTabs({ modules, selectedId, onSelect, footer }: ModuleTabsProps) {
  const { state } = useRunsStore();

  return (
    <aside className="sidebar">
      <nav
        className="side-tabs"
        role="tablist"
        aria-orientation="vertical"
        aria-label="Fonctionnalités"
      >
        {modules.map(({ manifest }) => {
          const entry = entryFor(state, manifest.id);
          const isSelected = manifest.id === selectedId;
          return (
            <button
              key={manifest.id}
              type="button"
              role="tab"
              aria-selected={isSelected}
              aria-controls={tabPanelId(manifest.id)}
              className={isSelected ? "side-tab selected" : "side-tab"}
              onClick={() => {
                onSelect(manifest.id);
              }}
            >
              <span className="side-tab-label">
                <ModuleIconView name={manifest.icon} />
                {manifest.name}
              </span>
              <TabRunBadge status={entry.run.status} unseen={entry.unseenOutcome && !isSelected} />
            </button>
          );
        })}
      </nav>
      <div className="sidebar-footer">{footer}</div>
    </aside>
  );
}

function TabRunBadge({ status, unseen }: { status: RunStatus; unseen: boolean }) {
  if (status === "running") {
    return <Spinner label="En cours" />;
  }
  if (!unseen) {
    return null;
  }
  return <span className={`status-dot ${status === "succeeded" ? "ready" : "failed"}`} />;
}

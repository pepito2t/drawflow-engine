import { t } from "../i18n/shell";
import type { ReactNode } from "react";
import { useRunsStore } from "../hooks/runs-context";
import type { CatalogModule } from "../lib/catalog";
import { entryFor } from "../lib/runs-store";
import type { RunStatus } from "../lib/run-state";
import { ModuleIconView } from "./ModuleIconView";
import { Spinner } from "./Spinner";

export interface ExtraTab {
  id: string;
  label: string;
  icon: ReactNode;
}

interface ModuleTabsProps {
  modules: CatalogModule[];
  leadingTabs: ExtraTab[];
  extraTabs: ExtraTab[];
  selectedId: string | null;
  onSelect: (tabId: string) => void;
  footer: ReactNode;
}

export const tabPanelId = (moduleId: string) => `panel-${moduleId}`;

export function ModuleTabs({
  modules,
  leadingTabs,
  extraTabs,
  selectedId,
  onSelect,
  footer,
}: ModuleTabsProps) {
  const { state } = useRunsStore();

  return (
    <aside className="sidebar">
      <nav
        className="side-tabs"
        role="tablist"
        aria-orientation="vertical"
        aria-label={t("moduleTabs.title")}
      >
        {leadingTabs.map((tab) => (
          <ExtraTabButton
            key={tab.id}
            tab={tab}
            selected={tab.id === selectedId}
            onSelect={onSelect}
          />
        ))}
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
        {extraTabs.map((tab) => (
          <ExtraTabButton
            key={tab.id}
            tab={tab}
            selected={tab.id === selectedId}
            onSelect={onSelect}
            separated
          />
        ))}
      </nav>
      <div className="sidebar-footer">{footer}</div>
    </aside>
  );
}

interface ExtraTabButtonProps {
  tab: ExtraTab;
  selected: boolean;
  onSelect: (tabId: string) => void;
  separated?: boolean;
}

function ExtraTabButton({ tab, selected, onSelect, separated = false }: ExtraTabButtonProps) {
  const classes = ["side-tab", selected ? "selected" : "", separated ? "side-tab-extra" : ""];
  return (
    <button
      type="button"
      role="tab"
      aria-selected={selected}
      aria-controls={tabPanelId(tab.id)}
      className={classes.filter(Boolean).join(" ")}
      onClick={() => {
        onSelect(tab.id);
      }}
    >
      <span className="side-tab-label">
        {tab.icon}
        {tab.label}
      </span>
    </button>
  );
}

function TabRunBadge({ status, unseen }: { status: RunStatus; unseen: boolean }) {
  if (status === "running") {
    return <Spinner label={t("moduleTabs.running")} />;
  }
  if (!unseen) {
    return null;
  }
  return <span className={`status-dot ${status === "succeeded" ? "ready" : "failed"}`} />;
}

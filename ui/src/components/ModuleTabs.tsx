import type { CatalogModule } from "../lib/catalog";

interface ModuleTabsProps {
  modules: CatalogModule[];
  selectedId: string | null;
  onSelect: (moduleId: string) => void;
}

export const tabPanelId = (moduleId: string) => `panel-${moduleId}`;

export function ModuleTabs({ modules, selectedId, onSelect }: ModuleTabsProps) {
  return (
    <nav
      className="side-tabs"
      role="tablist"
      aria-orientation="vertical"
      aria-label="Fonctionnalités"
    >
      {modules.map(({ manifest }) => (
        <button
          key={manifest.id}
          type="button"
          role="tab"
          aria-selected={manifest.id === selectedId}
          aria-controls={tabPanelId(manifest.id)}
          className={manifest.id === selectedId ? "side-tab selected" : "side-tab"}
          onClick={() => {
            onSelect(manifest.id);
          }}
        >
          {manifest.name}
        </button>
      ))}
    </nav>
  );
}

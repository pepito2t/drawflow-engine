import type { CatalogModule } from "../lib/catalog";

interface ModuleTabsProps {
  modules: CatalogModule[];
  selectedId: string | null;
  onSelect: (moduleId: string | null) => void;
}

export const tabPanelId = (moduleId: string | null) => `panel-${moduleId ?? "welcome"}`;

export function ModuleTabs({ modules, selectedId, onSelect }: ModuleTabsProps) {
  const tabs = [
    { id: null, label: "Comment ça marche" },
    ...modules.map(({ manifest }) => ({ id: manifest.id, label: manifest.name })),
  ];

  return (
    <div className="tab-bar" role="tablist" aria-label="Fonctionnalités">
      {tabs.map((tab) => (
        <button
          key={tab.id ?? "welcome"}
          type="button"
          role="tab"
          aria-selected={tab.id === selectedId}
          aria-controls={tabPanelId(tab.id)}
          className={tab.id === selectedId ? "tab selected" : "tab"}
          onClick={() => {
            onSelect(tab.id);
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

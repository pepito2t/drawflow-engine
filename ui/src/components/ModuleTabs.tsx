import type { CatalogModule } from "../lib/catalog";

export type Selection = { kind: "module"; id: string } | { kind: "settings" };

interface ModuleTabsProps {
  modules: CatalogModule[];
  selection: Selection | null;
  onSelect: (selection: Selection) => void;
}

export const tabPanelId = (moduleId: string) => `panel-${moduleId}`;
export const SETTINGS_PANEL_ID = "panel-settings";

export function ModuleTabs({ modules, selection, onSelect }: ModuleTabsProps) {
  const isModuleSelected = (id: string) => selection?.kind === "module" && selection.id === id;
  const isSettingsSelected = selection?.kind === "settings";

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
          aria-selected={isModuleSelected(manifest.id)}
          aria-controls={tabPanelId(manifest.id)}
          className={isModuleSelected(manifest.id) ? "side-tab selected" : "side-tab"}
          onClick={() => {
            onSelect({ kind: "module", id: manifest.id });
          }}
        >
          {manifest.name}
        </button>
      ))}
      <button
        type="button"
        role="tab"
        aria-selected={isSettingsSelected}
        aria-controls={SETTINGS_PANEL_ID}
        className={isSettingsSelected ? "side-tab settings-tab selected" : "side-tab settings-tab"}
        onClick={() => {
          onSelect({ kind: "settings" });
        }}
      >
        Paramètres
      </button>
    </nav>
  );
}

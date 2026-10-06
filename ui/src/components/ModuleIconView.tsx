import type { ModuleIconName } from "../lib/catalog";
import { CheckIcon, DiffIcon, ListIcon, ModuleIcon, ReportIcon, TableIcon } from "./icons";

const NAV_ICON_SIZE = 16;

const ICONS: Record<ModuleIconName, typeof ModuleIcon> = {
  module: ModuleIcon,
  list: ListIcon,
  report: ReportIcon,
  table: TableIcon,
  check: CheckIcon,
  diff: DiffIcon,
};

export function ModuleIconView({ name }: { name: ModuleIconName }) {
  const Icon = ICONS[name];
  return <Icon size={NAV_ICON_SIZE} />;
}

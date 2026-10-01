import type { ReactNode } from "react";
import { StatusBar, type EngineStatus } from "./StatusBar";

interface AppShellProps {
  engine: EngineStatus;
  canInstallUpdate?: boolean;
  children: ReactNode;
}

export function AppShell({ engine, canInstallUpdate = true, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <div className="app-content">{children}</div>
      <StatusBar engine={engine} canInstallUpdate={canInstallUpdate} />
    </div>
  );
}

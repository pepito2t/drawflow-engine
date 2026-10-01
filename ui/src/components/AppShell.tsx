import type { ReactNode } from "react";
import { StatusBar, type EngineStatus } from "./StatusBar";

interface AppShellProps {
  engine: EngineStatus;
  updates?: ReactNode;
  children: ReactNode;
}

export function AppShell({ engine, updates, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <div className="app-content">{children}</div>
      <StatusBar engine={engine} updates={updates} />
    </div>
  );
}

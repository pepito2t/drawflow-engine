import type { ReactNode } from "react";
import { useLanguage } from "../hooks/use-language";
import { ConsoleDock } from "./ConsoleDock";
import { StatusBar, type EngineStatus } from "./StatusBar";

interface AppShellProps {
  engine: EngineStatus;
  updates?: ReactNode;
  children: ReactNode;
}

export function AppShell({ engine, updates, children }: AppShellProps) {
  useLanguage();
  return (
    <div className="app-shell">
      <div className="app-content">{children}</div>
      <ConsoleDock />
      <StatusBar engine={engine} updates={updates} />
    </div>
  );
}

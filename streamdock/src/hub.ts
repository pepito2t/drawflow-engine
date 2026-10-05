import { DrawflowClient, type ConnectionState, type SocketLike } from "./drawflow-client";
import { appStateSchema, type AppState, type CommandResult } from "./protocol";
import { acknowledge, applyEvent, runsFromState, type Runs } from "./run-tracker";

const EMPTY_STATE: AppState = { modules: [], presets: [], runs: [] };

/** Shared view of Drawflow for every key: connection, features, presets and runs. */
export class DrawflowHub {
  connection: ConnectionState = "offline";
  app: AppState = EMPTY_STATE;
  runs: Runs = new Map();
  private readonly listeners = new Set<() => void>();
  private readonly client: DrawflowClient;

  constructor(createSocket: (url: string) => SocketLike) {
    this.client = new DrawflowClient({ createSocket });
    this.client.onState((state) => {
      this.connection = state;
      if (state === "ready") {
        this.refresh().catch(() => undefined);
      }
      this.notify();
    });
    this.client.onEvent((event) => {
      this.runs = applyEvent(this.runs, event);
      if (isRecord(event) && event.type === "presetSaved") {
        this.refresh().catch(() => undefined);
      }
      this.notify();
    });
  }

  configure(port: number, token: string): void {
    this.client.configure(token ? { port, token } : null);
  }

  onChange(listener: () => void): void {
    this.listeners.add(listener);
  }

  command(command: string, args: Record<string, unknown> = {}): Promise<CommandResult> {
    return this.client.command(command, args);
  }

  acknowledge(moduleId: string): void {
    this.runs = acknowledge(this.runs, moduleId);
    this.notify();
  }

  moduleName(moduleId: string): string {
    return this.app.modules.find((module) => module.id === moduleId)?.name ?? "Drawflow";
  }

  presetModule(presetId: string): { name: string; module: string } | null {
    return this.app.presets.find((preset) => preset.id === presetId) ?? null;
  }

  async refresh(): Promise<void> {
    const result = await this.client.command("app.state");
    if (!result.ok) {
      return;
    }
    const parsed = appStateSchema.safeParse(result.data);
    if (parsed.success) {
      this.app = parsed.data;
      this.runs = runsFromState(parsed.data);
      this.notify();
    }
  }

  private notify(): void {
    for (const listener of this.listeners) listener();
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

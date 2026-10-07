import {
  DEFAULT_TIMERS,
  DrawflowClient,
  type Connection,
  type ConnectionState,
  type SocketLike,
  type Timers,
} from "./drawflow-client";
import { appStateSchema, type AppState, type CommandResult } from "./protocol";
import { acknowledge, applyEvent, runningCount, runsFromState, type Runs } from "./run-tracker";

const EMPTY_STATE: AppState = { modules: [], presets: [], runs: [] };
// Drawflow's relay may drop events under load; a periodic reload catches a missed `runFinished`.
const RESYNC_WHILE_RUNNING_MS = 30_000;
const RESYNC_EVENTS: ReadonlySet<string> = new Set(["presetSaved", "resync"]);
const UNREADABLE_STATE_ERROR = "Réponse de Drawflow illisible : mettez à jour le plugin.";

/** Shared view of Drawflow for every key: connection, features, presets and runs. */
export class DrawflowHub {
  connection: ConnectionState = "offline";
  app: AppState = EMPTY_STATE;
  runs: Runs = new Map();
  private readonly listeners = new Set<() => void>();
  private readonly client: DrawflowClient;
  private readonly timers: Timers;
  private manual: Connection | null = null;
  private automatic: Connection | null = null;
  private resyncTimer: unknown = null;

  constructor(createSocket: (url: string) => SocketLike, timers: Partial<Timers> = {}) {
    this.timers = { ...DEFAULT_TIMERS, ...timers };
    this.client = new DrawflowClient({ createSocket, ...timers });
    this.client.onState((state) => {
      this.connection = state;
      if (state === "ready") {
        this.resync();
      }
      this.notify();
    });
    this.client.onEvent((event) => {
      this.runs = applyEvent(this.runs, event);
      if (isRecord(event) && typeof event.type === "string" && RESYNC_EVENTS.has(event.type)) {
        this.resync();
      }
      this.notify();
    });
  }

  /** What was typed in a key: only used when Drawflow's own settings cannot be read. */
  configure(port: number, token: string): void {
    this.manual = token ? { port, token } : null;
    this.apply();
  }

  setAutomatic(connection: Connection | null): void {
    this.automatic = connection;
    this.apply();
  }

  private apply(): void {
    this.client.configure(this.automatic ?? this.manual);
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

  /** Reloads features, presets and runs from Drawflow. */
  async refresh(): Promise<CommandResult> {
    const result = await this.client.command("app.state");
    if (!result.ok) {
      return result;
    }
    const parsed = appStateSchema.safeParse(result.data);
    if (!parsed.success) {
      return { ok: false, error: UNREADABLE_STATE_ERROR };
    }
    this.app = parsed.data;
    this.runs = runsFromState(parsed.data);
    this.notify();
    return { ok: true };
  }

  private resync(): void {
    this.refresh()
      .then(() => {
        this.scheduleResync();
      })
      .catch((error: unknown) => {
        console.error("Resynchronisation avec Drawflow impossible :", error);
      });
  }

  private scheduleResync(): void {
    const needed = this.connection === "ready" && runningCount(this.runs) > 0;
    if (needed && this.resyncTimer === null) {
      this.resyncTimer = this.timers.setTimer(() => {
        this.resyncTimer = null;
        this.resync();
      }, RESYNC_WHILE_RUNNING_MS);
    } else if (!needed && this.resyncTimer !== null) {
      this.timers.clearTimer(this.resyncTimer);
      this.resyncTimer = null;
    }
  }

  private notify(): void {
    this.scheduleResync();
    for (const listener of this.listeners) listener();
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

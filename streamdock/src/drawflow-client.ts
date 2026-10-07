import {
  PROTOCOL_VERSION,
  serverMessageSchema,
  type CommandResult,
  type ServerMessage,
} from "./protocol";

/** `refused`: Drawflow rejected the token; nothing to retry until the settings change. */
export type ConnectionState = "offline" | "locked" | "ready" | "refused";

/** Minimal socket surface, implemented by `ws` in production and by fakes in tests. */
export interface SocketLike {
  send: (data: string) => void;
  close: () => void;
  onOpen: (listener: () => void) => void;
  onMessage: (listener: (data: string) => void) => void;
  onClose: (listener: () => void) => void;
}

export interface Timers {
  setTimer: (callback: () => void, delayMs: number) => unknown;
  clearTimer: (timer: unknown) => void;
}

export interface ClientOptions extends Partial<Timers> {
  createSocket: (url: string) => SocketLike;
}

export const DEFAULT_TIMERS: Timers = {
  setTimer: (callback, delayMs) => setTimeout(callback, delayMs),
  clearTimer: (timer) => {
    clearTimeout(timer as ReturnType<typeof setTimeout>);
  },
};

export interface Connection {
  port: number;
  token: string;
}

const COMMAND_TIMEOUT_MS = 20_000;
const MIN_RECONNECT_MS = 2_000;
const MAX_RECONNECT_MS = 15_000;
const OFFLINE_ERROR = "Drawflow n'est pas joignable (application fermée ou API locale désactivée).";
const LOCKED_ERROR = "Drawflow est verrouillée : saisissez le code d'accès dans l'application.";
const REFUSED_ERROR =
  "Jeton refusé par Drawflow : vérifiez le jeton dans les réglages de la touche.";

const COMMAND_ERRORS: Record<Exclude<ConnectionState, "ready">, string> = {
  offline: OFFLINE_ERROR,
  locked: LOCKED_ERROR,
  refused: REFUSED_ERROR,
};

interface Pending {
  resolve: (result: CommandResult) => void;
  timer: unknown;
}

/** Keeps a WebSocket open to Drawflow's local API, reconnecting with backoff. */
export class DrawflowClient {
  state: ConnectionState = "offline";
  private socket: SocketLike | null = null;
  private connection: Connection | null = null;
  private nextId = 1;
  private reconnectDelay = MIN_RECONNECT_MS;
  private reconnectTimer: unknown = null;
  private readonly pending = new Map<string, Pending>();
  private readonly stateListeners = new Set<(state: ConnectionState) => void>();
  private readonly eventListeners = new Set<(event: unknown) => void>();
  private readonly setTimer: Timers["setTimer"];
  private readonly clearTimer: Timers["clearTimer"];

  constructor(private readonly options: ClientOptions) {
    this.setTimer = options.setTimer ?? DEFAULT_TIMERS.setTimer;
    this.clearTimer = options.clearTimer ?? DEFAULT_TIMERS.clearTimer;
  }

  configure(connection: Connection | null): void {
    const changed =
      connection?.port !== this.connection?.port || connection?.token !== this.connection?.token;
    if (!changed) {
      return;
    }
    this.connection = connection;
    this.disconnect();
    this.connect();
  }

  onState(listener: (state: ConnectionState) => void): void {
    this.stateListeners.add(listener);
  }

  onEvent(listener: (event: unknown) => void): void {
    this.eventListeners.add(listener);
  }

  command(command: string, args: Record<string, unknown> = {}): Promise<CommandResult> {
    if (this.state !== "ready") {
      return Promise.resolve({ ok: false, error: COMMAND_ERRORS[this.state] });
    }
    if (this.socket === null) {
      return Promise.resolve({ ok: false, error: OFFLINE_ERROR });
    }
    const id = String(this.nextId++);
    const socket = this.socket;
    return new Promise((resolve) => {
      const timer = this.setTimer(() => {
        this.pending.delete(id);
        resolve({ ok: false, error: "Drawflow n'a pas répondu à temps." });
      }, COMMAND_TIMEOUT_MS);
      this.pending.set(id, { resolve, timer });
      socket.send(JSON.stringify({ type: "command", id, command, args }));
    });
  }

  private connect(): void {
    if (this.connection === null || !this.connection.token) {
      return;
    }
    const { port, token } = this.connection;
    const socket = this.options.createSocket(`ws://127.0.0.1:${String(port)}`);
    this.socket = socket;
    socket.onOpen(() => {
      socket.send(JSON.stringify({ type: "hello", token, version: PROTOCOL_VERSION }));
    });
    socket.onMessage((data) => {
      this.handle(data);
    });
    socket.onClose(() => {
      if (this.socket === socket) {
        this.socket = null;
        this.setState("offline");
        this.failPending(OFFLINE_ERROR);
        this.scheduleReconnect();
      }
    });
  }

  private disconnect(): void {
    if (this.reconnectTimer !== null) {
      this.clearTimer(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    const socket = this.socket;
    this.socket = null;
    socket?.close();
    this.failPending(OFFLINE_ERROR);
    this.setState("offline");
  }

  private scheduleReconnect(): void {
    if (this.connection === null) {
      return;
    }
    this.reconnectTimer = this.setTimer(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, MAX_RECONNECT_MS);
  }

  private handle(data: string): void {
    let parsed: ServerMessage;
    try {
      parsed = serverMessageSchema.parse(JSON.parse(data));
    } catch {
      return;
    }
    switch (parsed.type) {
      case "welcome":
        this.reconnectDelay = MIN_RECONNECT_MS;
        this.setState(parsed.locked ? "locked" : "ready");
        return;
      case "locked":
        this.setState(parsed.locked ? "locked" : "ready");
        return;
      case "error":
        this.refuse();
        return;
      case "result":
        this.resolve(
          parsed.id,
          parsed.ok
            ? { ok: true, data: parsed.data }
            : { ok: false, error: parsed.error ?? "Erreur inconnue." },
        );
        return;
      case "event":
        for (const listener of this.eventListeners) listener(parsed.event);
    }
  }

  /** Drawflow only sends `error` instead of `welcome`: the token is wrong, retrying is pointless. */
  private refuse(): void {
    const socket = this.socket;
    this.socket = null;
    this.failPending(REFUSED_ERROR);
    this.setState("refused");
    socket?.close();
  }

  private resolve(id: string, result: CommandResult): void {
    const pending = this.pending.get(id);
    if (pending) {
      this.clearTimer(pending.timer);
      this.pending.delete(id);
      pending.resolve(result);
    }
  }

  private failPending(error: string): void {
    for (const [id] of this.pending) this.resolve(id, { ok: false, error });
  }

  private setState(state: ConnectionState): void {
    if (state === this.state) {
      return;
    }
    this.state = state;
    for (const listener of this.stateListeners) listener(state);
  }
}

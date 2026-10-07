import * as z from "zod/mini";
import type { SocketLike } from "./drawflow-client";

/** How Stream Dock starts the plugin: `-port 1234 -pluginUUID … -registerEvent … -info {…}`. */
export interface LaunchArguments {
  port: number;
  pluginUUID: string;
  registerEvent: string;
}

const hostEventSchema = z.object({
  event: z.string(),
  action: z.optional(z.string()),
  context: z.optional(z.string()),
  payload: z.optional(z.record(z.string(), z.unknown())),
});

export type HostEvent = z.infer<typeof hostEventSchema>;
type Payload = Record<string, unknown>;

export class LaunchError extends Error {
  override name = "LaunchError";
}

export function parseLaunchArguments(argv: readonly string[]): LaunchArguments {
  const value = (flag: string): string => {
    const index = argv.indexOf(flag);
    const found = index === -1 ? undefined : argv[index + 1];
    if (found === undefined) {
      throw new LaunchError(
        `Argument ${flag} manquant : le plugin doit être lancé par Stream Dock.`,
      );
    }
    return found;
  };
  const port = Number(value("-port"));
  if (!Number.isInteger(port) || port <= 0) {
    throw new LaunchError("Port de Stream Dock invalide.");
  }
  return { port, pluginUUID: value("-pluginUUID"), registerEvent: value("-registerEvent") };
}

/** The plugin side of the Stream Dock protocol (same messages as the classic Stream Deck SDK). */
export class StreamDockHost {
  private readonly listeners = new Set<(event: HostEvent) => void>();

  constructor(
    private readonly socket: SocketLike,
    launch: LaunchArguments,
  ) {
    socket.onOpen(() => {
      this.send({ event: launch.registerEvent, uuid: launch.pluginUUID });
      this.send({ event: "getGlobalSettings", context: launch.pluginUUID });
    });
    socket.onMessage((data) => {
      const event = parseHostEvent(data);
      if (event !== null) {
        for (const listener of this.listeners) listener(event);
      }
    });
  }

  onEvent(listener: (event: HostEvent) => void): void {
    this.listeners.add(listener);
  }

  setImage(context: string, image: string): void {
    this.send({ event: "setImage", context, payload: { image, target: 0 } });
  }

  setTitle(context: string, title: string): void {
    this.send({ event: "setTitle", context, payload: { title, target: 0 } });
  }

  showAlert(context: string): void {
    this.send({ event: "showAlert", context });
  }

  showOk(context: string): void {
    this.send({ event: "showOk", context });
  }

  sendToPropertyInspector(action: string, context: string, payload: Payload): void {
    this.send({ event: "sendToPropertyInspector", action, context, payload });
  }

  private send(message: Payload): void {
    this.socket.send(JSON.stringify(message));
  }
}

export function parseHostEvent(data: string): HostEvent | null {
  try {
    const parsed = hostEventSchema.safeParse(JSON.parse(data));
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

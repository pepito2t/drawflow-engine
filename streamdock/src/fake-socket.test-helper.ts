import type { SocketLike } from "./drawflow-client";

/** In-memory socket: records what the plugin sends and lets a test play the other side. */
export class FakeSocket implements SocketLike {
  readonly sent: Record<string, unknown>[] = [];
  private openListener: () => void = () => undefined;
  private messageListener: (data: string) => void = () => undefined;

  send(data: string): void {
    this.sent.push(JSON.parse(data) as Record<string, unknown>);
  }

  close(): void {
    return undefined;
  }

  onOpen(listener: () => void): void {
    this.openListener = listener;
  }

  onMessage(listener: (data: string) => void): void {
    this.messageListener = listener;
  }

  onClose(): void {
    return undefined;
  }

  open(): void {
    this.openListener();
  }

  receive(message: object): void {
    this.messageListener(JSON.stringify(message));
  }

  sentEvents(): unknown[] {
    return this.sent.map((message) => message.event);
  }
}

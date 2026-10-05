import WebSocket from "ws";
import type { SocketLike } from "./drawflow-client";

export function createWsSocket(url: string): SocketLike {
  const socket = new WebSocket(url);
  // Connection failures surface as "close"; logging each retry would flood the plugin log.
  socket.on("error", () => undefined);
  return {
    send: (data) => {
      socket.send(data);
    },
    close: () => {
      socket.close();
    },
    onOpen: (listener) => socket.on("open", listener),
    onMessage: (listener) =>
      socket.on("message", (data: WebSocket.RawData) => {
        listener(
          Buffer.isBuffer(data)
            ? data.toString("utf8")
            : Buffer.concat(Array.isArray(data) ? data : [Buffer.from(data)]).toString("utf8"),
        );
      }),
    onClose: (listener) => socket.on("close", listener),
  };
}

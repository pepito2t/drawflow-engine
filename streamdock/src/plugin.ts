import { readFileSync } from "node:fs";
import { sep } from "node:path";
import { loadDrawflowConnection } from "./drawflow-config";
import { StreamDockHost, parseLaunchArguments } from "./host";
import { DrawflowHub } from "./hub";
import { KeyController } from "./keys";
import { createWsSocket } from "./ws-socket";

// Drawflow may be installed, enabled or given a new token while the plugin runs.
const AUTO_CONFIG_INTERVAL_MS = 5000;

function readFile(path: string): string | null {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return null;
  }
}

const launch = parseLaunchArguments(process.argv);
const hostSocket = createWsSocket(`ws://127.0.0.1:${String(launch.port)}`);
hostSocket.onClose(() => process.exit(0));

const hub = new DrawflowHub(createWsSocket);
const autoConfigure = (): void => {
  hub.setAutomatic(loadDrawflowConnection(readFile, process.env, sep));
};
autoConfigure();
setInterval(autoConfigure, AUTO_CONFIG_INTERVAL_MS);

new KeyController(new StreamDockHost(hostSocket, launch), hub);

import { StreamDockHost, parseLaunchArguments } from "./host";
import { DrawflowHub } from "./hub";
import { KeyController } from "./keys";
import { createWsSocket } from "./ws-socket";

const launch = parseLaunchArguments(process.argv);
const hostSocket = createWsSocket(`ws://127.0.0.1:${String(launch.port)}`);
hostSocket.onClose(() => process.exit(0));

new KeyController(new StreamDockHost(hostSocket, launch), new DrawflowHub(createWsSocket));

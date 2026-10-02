import streamDeck from "@elgato/streamdeck";
import { CancelAllAction, OpenLastResultAction, RunsCounterAction } from "./actions/simple";
import { OpenTabAction } from "./actions/open-tab";
import { PresetAction } from "./actions/preset";
import { DrawflowHub } from "./hub";
import { createWsSocket } from "./ws-socket";

const DEFAULT_PORT = 51717;

type GlobalSettings = { port?: string | number; token?: string };

const hub = new DrawflowHub(createWsSocket);

function applyGlobalSettings(settings: GlobalSettings): void {
  const port = Number(settings.port ?? DEFAULT_PORT);
  hub.configure(
    Number.isInteger(port) && port > 0 ? port : DEFAULT_PORT,
    (settings.token ?? "").trim(),
  );
}

streamDeck.actions.registerAction(new PresetAction(hub));
streamDeck.actions.registerAction(new OpenTabAction(hub));
streamDeck.actions.registerAction(new CancelAllAction(hub));
streamDeck.actions.registerAction(new OpenLastResultAction(hub));
streamDeck.actions.registerAction(new RunsCounterAction(hub));

streamDeck.settings.onDidReceiveGlobalSettings<GlobalSettings>((ev) => {
  applyGlobalSettings(ev.settings);
});

await streamDeck.connect();
applyGlobalSettings(await streamDeck.settings.getGlobalSettings<GlobalSettings>());

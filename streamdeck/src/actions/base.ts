import streamDeck, {
  SingletonAction,
  type KeyAction,
  type SendToPluginEvent,
} from "@elgato/streamdeck";
import type { JsonObject } from "@elgato/utils";
import type { DrawflowHub } from "../hub";
import { renderKey, type KeyFace } from "../key-image";

/** Common behaviour: re-render every visible key when Drawflow's state changes. */
export abstract class DrawflowAction<
  Settings extends JsonObject,
> extends SingletonAction<Settings> {
  private readonly settingsById = new Map<string, Settings>();

  constructor(protected readonly hub: DrawflowHub) {
    super();
    hub.onChange(() => {
      this.renderAll().catch((error: unknown) => {
        streamDeck.logger.error(`Rendu impossible : ${String(error)}`);
      });
    });
  }

  protected abstract face(settings: Settings): KeyFace;

  protected remember(id: string, settings: Settings): void {
    this.settingsById.set(id, settings);
  }

  protected async render(action: KeyAction<Settings>, settings: Settings): Promise<void> {
    this.remember(action.id, settings);
    await action.setTitle("");
    await action.setImage(renderKey(this.face(settings)));
  }

  protected async renderAll(): Promise<void> {
    for (const action of this.actions) {
      if (action.isKey()) {
        const settings = this.settingsById.get(action.id) ?? (await action.getSettings());
        await this.render(action, settings);
      }
    }
  }

  override async onSendToPlugin(ev: SendToPluginEvent<JsonObject, Settings>): Promise<void> {
    const request = ev.payload.event;
    if (request === "getPresets") {
      const items = this.hub.app.presets.map((preset) => ({
        label: `${preset.name} (${this.hub.moduleName(preset.module)})`,
        value: preset.id,
      }));
      await streamDeck.ui.sendToPropertyInspector({ event: "getPresets", items });
    } else if (request === "getModules") {
      const items = this.hub.app.modules.map((module) => ({
        label: module.name,
        value: module.id,
      }));
      await streamDeck.ui.sendToPropertyInspector({ event: "getModules", items });
    }
  }
}

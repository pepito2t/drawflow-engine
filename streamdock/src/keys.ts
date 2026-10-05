import { BEHAVIORS, type Settings } from "./behaviors";
import type { HostEvent, StreamDockHost } from "./host";
import type { DrawflowHub } from "./hub";
import { renderKey } from "./key-image";

interface VisibleKey {
  action: string;
  settings: Settings;
}

const DEFAULT_PORT = 51717;

/** Keeps every visible key in sync with Drawflow and runs its command when pressed. */
export class KeyController {
  private readonly keys = new Map<string, VisibleKey>();

  constructor(
    private readonly host: StreamDockHost,
    private readonly hub: DrawflowHub,
  ) {
    host.onEvent((event) => {
      this.handle(event).catch((error: unknown) => {
        console.error(`Événement ${event.event} non traité :`, error);
      });
    });
    hub.onChange(() => {
      for (const context of this.keys.keys()) this.render(context);
    });
  }

  private async handle(event: HostEvent): Promise<void> {
    const { context, action } = event;
    const settings = (event.payload?.settings ?? {}) as Settings;
    switch (event.event) {
      case "didReceiveGlobalSettings":
        this.configure(settings);
        return;
      case "willAppear":
      case "didReceiveSettings":
        if (context && action && action in BEHAVIORS) {
          this.keys.set(context, { action, settings });
          this.render(context);
        }
        return;
      case "willDisappear":
        if (context) this.keys.delete(context);
        return;
      case "keyUp":
        if (context) await this.press(context);
        return;
      case "sendToPlugin":
        if (context && action) this.answerInspector(action, context, event.payload ?? {});
        return;
    }
  }

  private configure(settings: Settings): void {
    const port = Number(settings.port ?? DEFAULT_PORT);
    const token = typeof settings.token === "string" ? settings.token.trim() : "";
    this.hub.configure(Number.isInteger(port) && port > 0 ? port : DEFAULT_PORT, token);
  }

  private render(context: string): void {
    const key = this.keys.get(context);
    const behavior = key ? BEHAVIORS[key.action] : undefined;
    if (key && behavior) {
      this.host.setTitle(context, "");
      this.host.setImage(context, renderKey(behavior.face(this.hub, key.settings)));
    }
  }

  private async press(context: string): Promise<void> {
    const key = this.keys.get(context);
    const behavior = key ? BEHAVIORS[key.action] : undefined;
    if (!key || !behavior) {
      return;
    }
    const outcome = await behavior.press(this.hub, key.settings);
    if (outcome === "ok") this.host.showOk(context);
    if (outcome === "alert") this.host.showAlert(context);
  }

  private answerInspector(action: string, context: string, request: Settings): void {
    if (request.event === "getPresets") {
      const items = this.hub.app.presets.map((preset) => ({
        label: `${preset.name} (${this.hub.moduleName(preset.module)})`,
        value: preset.id,
      }));
      this.host.sendToPropertyInspector(action, context, { event: "getPresets", items });
    } else if (request.event === "getModules") {
      const items = this.hub.app.modules.map((module) => ({
        label: module.name,
        value: module.id,
      }));
      this.host.sendToPropertyInspector(action, context, { event: "getModules", items });
    }
  }
}

import { BEHAVIORS, type Settings } from "./behaviors";
import { commandChoices } from "./commands";
import { DEFAULT_TIMERS, type Timers } from "./drawflow-client";
import type { HostEvent, StreamDockHost } from "./host";
import type { DrawflowHub } from "./hub";
import { renderKey } from "./key-image";

interface VisibleKey {
  action: string;
  settings: Settings;
}

interface Notice {
  message: string;
  timer: unknown;
}

interface InspectorItem {
  label: string;
  value: string;
}

const DEFAULT_PORT = 51717;
const NOTICE_MS = 3_000;

/** Keeps every visible key in sync with Drawflow and runs its command when pressed. */
export class KeyController {
  private readonly keys = new Map<string, VisibleKey>();
  private readonly notices = new Map<string, Notice>();
  private readonly timers: Timers;

  constructor(
    private readonly host: StreamDockHost,
    private readonly hub: DrawflowHub,
    timers: Partial<Timers> = {},
  ) {
    this.timers = { ...DEFAULT_TIMERS, ...timers };
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
        if (context) {
          this.keys.delete(context);
          this.clearNotice(context);
        }
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
    if (!key || !behavior) {
      return;
    }
    const face = behavior.face(this.hub, key.settings);
    const notice = this.notices.get(context);
    this.host.setImage(
      context,
      renderKey(
        notice
          ? { tone: "failed", label: face.label, detail: notice.message, progress: null }
          : face,
      ),
    );
  }

  private async press(context: string): Promise<void> {
    const key = this.keys.get(context);
    const behavior = key ? BEHAVIORS[key.action] : undefined;
    if (!key || !behavior) {
      return;
    }
    const outcome = await behavior.press(this.hub, key.settings);
    if (outcome === "ok") {
      this.host.showOk(context);
    } else if (outcome !== "silent") {
      this.host.showAlert(context);
      this.showNotice(context, outcome.failed);
    }
  }

  private showNotice(context: string, message: string): void {
    this.clearNotice(context);
    const timer = this.timers.setTimer(() => {
      this.notices.delete(context);
      this.render(context);
    }, NOTICE_MS);
    this.notices.set(context, { message, timer });
    this.render(context);
  }

  private clearNotice(context: string): void {
    const notice = this.notices.get(context);
    if (notice) {
      this.timers.clearTimer(notice.timer);
      this.notices.delete(context);
    }
  }

  private answerInspector(action: string, context: string, request: Settings): void {
    const source = request.event;
    const items = typeof source === "string" ? this.inspectorItems(source) : null;
    if (typeof source === "string" && items !== null) {
      this.host.sendToPropertyInspector(action, context, {
        event: source,
        items,
        connection: this.hub.connection,
      });
    }
  }

  private inspectorItems(source: string): InspectorItem[] | null {
    switch (source) {
      case "getPresets":
        return this.presetItems();
      case "getModules":
        return this.moduleItems();
      case "getCommands":
        return commandChoices(this.hub.language);
      default:
        return null;
    }
  }

  private presetItems(): InspectorItem[] {
    return this.hub.app.presets.map((preset) => ({
      label: `${preset.name} (${this.hub.moduleName(preset.module)})`,
      value: preset.id,
    }));
  }

  private moduleItems(): InspectorItem[] {
    return this.hub.app.modules.map((module) => ({ label: module.name, value: module.id }));
  }
}

import {
  action,
  type DidReceiveSettingsEvent,
  type KeyDownEvent,
  type WillAppearEvent,
} from "@elgato/streamdeck";
import { faceFor, type KeyFace } from "../key-image";
import { runFor } from "../run-tracker";
import { DrawflowAction } from "./base";

type TabSettings = { moduleId?: string };

@action({ UUID: "ch.drawflow.open-tab" })
export class OpenTabAction extends DrawflowAction<TabSettings> {
  protected face(settings: TabSettings): KeyFace {
    if (!settings.moduleId) {
      return faceFor(this.hub.connection, "Choisir un onglet", null);
    }
    return faceFor(
      this.hub.connection,
      this.hub.moduleName(settings.moduleId),
      runFor(this.hub.runs, settings.moduleId),
    );
  }

  override async onWillAppear(ev: WillAppearEvent<TabSettings>): Promise<void> {
    if (ev.action.isKey()) await this.render(ev.action, ev.payload.settings);
  }

  override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<TabSettings>): Promise<void> {
    if (ev.action.isKey()) await this.render(ev.action, ev.payload.settings);
  }

  override async onKeyDown(ev: KeyDownEvent<TabSettings>): Promise<void> {
    const moduleId = ev.payload.settings.moduleId;
    if (!moduleId) {
      await ev.action.showAlert();
      return;
    }
    this.hub.acknowledge(moduleId);
    const result = await this.hub.command("tab.open", { moduleId });
    if (!result.ok) await ev.action.showAlert();
  }
}

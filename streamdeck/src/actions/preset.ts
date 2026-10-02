import {
  action,
  type DidReceiveSettingsEvent,
  type KeyDownEvent,
  type WillAppearEvent,
} from "@elgato/streamdeck";
import { faceFor, type KeyFace } from "../key-image";
import { runFor } from "../run-tracker";
import { DrawflowAction } from "./base";

type PresetSettings = { presetId?: string };

@action({ UUID: "ch.drawflow.preset" })
export class PresetAction extends DrawflowAction<PresetSettings> {
  protected face(settings: PresetSettings): KeyFace {
    const preset = settings.presetId ? this.hub.presetModule(settings.presetId) : null;
    if (preset === null) {
      return faceFor(
        this.hub.connection,
        settings.presetId ? "Préréglage supprimé" : "Choisir un préréglage",
        null,
      );
    }
    return faceFor(this.hub.connection, preset.name, runFor(this.hub.runs, preset.module));
  }

  override async onWillAppear(ev: WillAppearEvent<PresetSettings>): Promise<void> {
    if (ev.action.isKey()) await this.render(ev.action, ev.payload.settings);
  }

  override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<PresetSettings>): Promise<void> {
    if (ev.action.isKey()) await this.render(ev.action, ev.payload.settings);
  }

  override async onKeyDown(ev: KeyDownEvent<PresetSettings>): Promise<void> {
    const preset = ev.payload.settings.presetId
      ? this.hub.presetModule(ev.payload.settings.presetId)
      : null;
    if (preset === null) {
      await ev.action.showAlert();
      return;
    }
    this.hub.acknowledge(preset.module);
    const result = await this.hub.command("preset.run", { presetId: ev.payload.settings.presetId });
    if (!result.ok) await ev.action.showAlert();
  }
}

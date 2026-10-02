import { action, type KeyDownEvent, type WillAppearEvent } from "@elgato/streamdeck";
import { faceFor, type KeyFace } from "../key-image";
import { runningCount } from "../run-tracker";
import { DrawflowAction } from "./base";

type NoSettings = Record<string, never>;

abstract class CommandKey extends DrawflowAction<NoSettings> {
  protected abstract readonly command: string;

  override async onWillAppear(ev: WillAppearEvent<NoSettings>): Promise<void> {
    if (ev.action.isKey()) await this.render(ev.action, ev.payload.settings);
  }

  override async onKeyDown(ev: KeyDownEvent<NoSettings>): Promise<void> {
    const result = await this.hub.command(this.command);
    await (result.ok ? ev.action.showOk() : ev.action.showAlert());
  }
}

@action({ UUID: "ch.drawflow.cancel-all" })
export class CancelAllAction extends CommandKey {
  protected readonly command = "runs.cancel-all";

  protected face(): KeyFace {
    const running = runningCount(this.hub.runs);
    const face = faceFor(this.hub.connection, "Annuler", null);
    return face.tone === "idle" && running > 0
      ? { ...face, tone: "failed", detail: `${String(running)} en cours` }
      : face;
  }
}

@action({ UUID: "ch.drawflow.open-last" })
export class OpenLastResultAction extends CommandKey {
  protected readonly command = "result.open-last";

  protected face(): KeyFace {
    return faceFor(this.hub.connection, "Dernier résultat", null);
  }
}

@action({ UUID: "ch.drawflow.runs-counter" })
export class RunsCounterAction extends CommandKey {
  protected readonly command = "app.state";

  protected face(): KeyFace {
    const running = runningCount(this.hub.runs);
    const face = faceFor(this.hub.connection, "Traitements", null);
    if (face.tone !== "idle") {
      return face;
    }
    return running > 0
      ? {
          tone: "running",
          label: "Traitements",
          detail: `${String(running)} en cours`,
          progress: null,
        }
      : { ...face, detail: "Aucun" };
  }
}

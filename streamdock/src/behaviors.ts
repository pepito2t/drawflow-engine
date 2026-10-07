import { commandLabel } from "./commands";
import type { DrawflowHub } from "./hub";
import { translate, type MessageKey } from "./i18n";
import { faceFor, type KeyFace } from "./key-image";
import { runFor, runningCount } from "./run-tracker";

export type Settings = Record<string, unknown>;
/** `silent`: the key will show the run itself; `failed`: the message is shown on the key. */
export type PressOutcome = "ok" | "silent" | { failed: string };

/** What one kind of key shows and does; the host wiring stays in keys.ts. */
export interface KeyBehavior {
  face: (hub: DrawflowHub, settings: Settings) => KeyFace;
  press: (hub: DrawflowHub, settings: Settings) => Promise<PressOutcome>;
}

const text = (settings: Settings, name: string): string | null => {
  const value = settings[name];
  return typeof value === "string" && value !== "" ? value : null;
};

const message = (hub: DrawflowHub, key: MessageKey, params?: Record<string, string>): string =>
  translate(hub.language, key, params);

const preset: KeyBehavior = {
  face(hub, settings) {
    const presetId = text(settings, "presetId");
    const found = presetId ? hub.presetModule(presetId) : null;
    if (found === null) {
      const label = message(hub, presetId ? "key.preset.gone" : "key.preset.choose");
      return faceFor(hub.language, hub.connection, label, null);
    }
    return faceFor(hub.language, hub.connection, found.name, runFor(hub.runs, found.module));
  },
  async press(hub, settings) {
    const presetId = text(settings, "presetId");
    if (presetId === null) {
      return { failed: message(hub, "error.presetNotChosen") };
    }
    const found = hub.presetModule(presetId);
    if (found === null) {
      return { failed: message(hub, "error.presetGone") };
    }
    hub.acknowledge(found.module);
    const result = await hub.command("preset.run", { presetId });
    return result.ok ? "silent" : { failed: result.error };
  },
};

const openTab: KeyBehavior = {
  face(hub, settings) {
    const moduleId = text(settings, "moduleId");
    if (moduleId === null) {
      return faceFor(hub.language, hub.connection, message(hub, "key.tab.choose"), null);
    }
    const label = hub.moduleName(moduleId);
    return faceFor(hub.language, hub.connection, label, runFor(hub.runs, moduleId));
  },
  async press(hub, settings) {
    const moduleId = text(settings, "moduleId");
    if (moduleId === null) {
      return { failed: message(hub, "error.tabNotChosen") };
    }
    hub.acknowledge(moduleId);
    const result = await hub.command("tab.open", { moduleId });
    return result.ok ? "silent" : { failed: result.error };
  },
};

function commandKey(command: string, face: KeyBehavior["face"]): KeyBehavior {
  return {
    face,
    async press(hub) {
      const result = await hub.command(command);
      return result.ok ? "ok" : { failed: result.error };
    },
  };
}

const cancelAll = commandKey("runs.cancel-all", (hub) => {
  const running = runningCount(hub.runs);
  const face = faceFor(hub.language, hub.connection, message(hub, "key.cancel"), null);
  return face.tone === "idle" && running > 0
    ? {
        ...face,
        tone: "warning",
        detail: message(hub, "key.runs.count", { count: String(running) }),
      }
    : face;
});

const openLast = commandKey("result.open-last", (hub) =>
  faceFor(hub.language, hub.connection, message(hub, "key.lastResult"), null),
);

const runsCounter: KeyBehavior = {
  face(hub) {
    const running = runningCount(hub.runs);
    const face = faceFor(hub.language, hub.connection, message(hub, "key.runs"), null);
    if (face.tone !== "idle") {
      return face;
    }
    return running > 0
      ? {
          ...face,
          tone: "running",
          detail: message(hub, "key.runs.count", { count: String(running) }),
        }
      : { ...face, detail: message(hub, "key.runs.none") };
  },
  async press(hub) {
    const result = await hub.refresh();
    return result.ok ? "ok" : { failed: result.error };
  },
};

const genericCommand: KeyBehavior = {
  face(hub, settings) {
    const commandId = text(settings, "commandId");
    const label = commandId === null ? null : commandLabel(hub.language, commandId);
    const shown = label ?? message(hub, commandId ? "key.command.gone" : "key.command.choose");
    return faceFor(hub.language, hub.connection, shown, null);
  },
  async press(hub, settings) {
    const commandId = text(settings, "commandId");
    if (commandId === null) {
      return { failed: message(hub, "error.commandNotChosen") };
    }
    if (commandLabel(hub.language, commandId) === null) {
      return { failed: message(hub, "error.commandGone") };
    }
    const result = await hub.command(commandId);
    return result.ok ? "ok" : { failed: result.error };
  },
};

export const BEHAVIORS: Readonly<Record<string, KeyBehavior>> = {
  "ch.drawflow.preset": preset,
  "ch.drawflow.open-tab": openTab,
  "ch.drawflow.cancel-all": cancelAll,
  "ch.drawflow.open-last": openLast,
  "ch.drawflow.runs-counter": runsCounter,
  "ch.drawflow.command": genericCommand,
};

import type { DrawflowHub } from "./hub";
import { faceFor, type KeyFace } from "./key-image";
import { runFor, runningCount } from "./run-tracker";

export type Settings = Record<string, unknown>;
export type PressOutcome = "ok" | "alert" | "silent";

/** What one kind of key shows and does; the host wiring stays in keys.ts. */
export interface KeyBehavior {
  face: (hub: DrawflowHub, settings: Settings) => KeyFace;
  press: (hub: DrawflowHub, settings: Settings) => Promise<PressOutcome>;
}

const text = (settings: Settings, name: string): string | null => {
  const value = settings[name];
  return typeof value === "string" && value !== "" ? value : null;
};

const preset: KeyBehavior = {
  face(hub, settings) {
    const presetId = text(settings, "presetId");
    const found = presetId ? hub.presetModule(presetId) : null;
    if (found === null) {
      return faceFor(
        hub.connection,
        presetId ? "Préréglage supprimé" : "Choisir un préréglage",
        null,
      );
    }
    return faceFor(hub.connection, found.name, runFor(hub.runs, found.module));
  },
  async press(hub, settings) {
    const presetId = text(settings, "presetId");
    const found = presetId ? hub.presetModule(presetId) : null;
    if (presetId === null || found === null) {
      return "alert";
    }
    hub.acknowledge(found.module);
    const result = await hub.command("preset.run", { presetId });
    return result.ok ? "silent" : "alert";
  },
};

const openTab: KeyBehavior = {
  face(hub, settings) {
    const moduleId = text(settings, "moduleId");
    if (moduleId === null) {
      return faceFor(hub.connection, "Choisir un onglet", null);
    }
    return faceFor(hub.connection, hub.moduleName(moduleId), runFor(hub.runs, moduleId));
  },
  async press(hub, settings) {
    const moduleId = text(settings, "moduleId");
    if (moduleId === null) {
      return "alert";
    }
    hub.acknowledge(moduleId);
    const result = await hub.command("tab.open", { moduleId });
    return result.ok ? "silent" : "alert";
  },
};

function commandKey(command: string, face: KeyBehavior["face"]): KeyBehavior {
  return {
    face,
    async press(hub) {
      const result = await hub.command(command);
      return result.ok ? "ok" : "alert";
    },
  };
}

const cancelAll = commandKey("runs.cancel-all", (hub) => {
  const running = runningCount(hub.runs);
  const face = faceFor(hub.connection, "Annuler", null);
  return face.tone === "idle" && running > 0
    ? { ...face, tone: "failed", detail: `${String(running)} en cours` }
    : face;
});

const openLast = commandKey("result.open-last", (hub) =>
  faceFor(hub.connection, "Dernier résultat", null),
);

const runsCounter = commandKey("app.state", (hub) => {
  const running = runningCount(hub.runs);
  const face = faceFor(hub.connection, "Traitements", null);
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
});

export const BEHAVIORS: Readonly<Record<string, KeyBehavior>> = {
  "ch.drawflow.preset": preset,
  "ch.drawflow.open-tab": openTab,
  "ch.drawflow.cancel-all": cancelAll,
  "ch.drawflow.open-last": openLast,
  "ch.drawflow.runs-counter": runsCounter,
};

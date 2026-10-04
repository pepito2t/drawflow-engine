import { z } from "zod";
import { CatalogError } from "./catalog";
import type { ReadableError } from "./error-message";
import { parseEventLine } from "./events";
import { parseJsonOrNull } from "./json";

const setupActionSchema = z.object({
  id: z.string(),
  label: z.string(),
  url: z.string().nullable(),
});

const setupReportSchema = z.object({
  system: z.object({
    os: z.enum(["windows", "macos", "linux"]),
    arch: z.string(),
    package_manager: z.enum(["winget", "brew"]).nullable(),
  }),
  items: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      status: z.enum(["ok", "missing", "optional"]),
      detail: z.string(),
      actions: z.array(setupActionSchema),
    }),
  ),
});

export type SetupReport = z.infer<typeof setupReportSchema>;
export type SetupItem = SetupReport["items"][number];
export type SetupActionSpec = z.infer<typeof setupActionSchema>;

/** Actions run by the engine; the others open a page in the browser. */
export const ENGINE_ACTIONS = [
  "oda.install",
  "oda.use-detected",
  "ollama.install",
  "ollama.start",
  "model.pull",
] as const;
export type EngineSetupAction = (typeof ENGINE_ACTIONS)[number];

const INSTALLS_THIRD_PARTY = new Set(["oda.install", "ollama.install", "model.pull"]);
export const SETUP_TAB_ID = "setup";
const PLUGIN_ACTION = "streamdeck.install-plugin";
const RELEASES_URL = "https://github.com/pepito2t/drawflow-engine/releases/download";
const PLUGIN_FILE = "ch.drawflow.streamDeckPlugin";
const OS_LABELS = { windows: "Windows", macos: "macOS", linux: "Linux" } as const;

export function parseSetupReport(rawJson: string): SetupReport {
  const parsed = setupReportSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError("L'analyse de l'installation reçue du moteur est invalide.");
  }
  return parsed.data;
}

export function isEngineAction(id: string): id is EngineSetupAction {
  return (ENGINE_ACTIONS as readonly string[]).includes(id);
}

export function needsConfirmation(id: string): boolean {
  return INSTALLS_THIRD_PARTY.has(id);
}

export function missingCount(report: SetupReport): number {
  return report.items.filter((item) => item.status === "missing").length;
}

export function describeSystem(report: SetupReport): string {
  const { os, arch, package_manager: manager } = report.system;
  return `${OS_LABELS[os]} · ${arch} · ${manager ?? "sans gestionnaire de paquets"}`;
}

/** The plugin attached to the release of the running version (the Stream Deck app opens it). */
export function pageFor(action: SetupActionSpec, appVersion: string): string | null {
  if (action.id === PLUGIN_ACTION) {
    return `${RELEASES_URL}/v${appVersion}/${PLUGIN_FILE}`;
  }
  return action.url;
}

export type SetupRun =
  | { status: "idle" }
  | { status: "running"; action: string; percent: number | null; message: string }
  | { status: "failed"; action: string; error: ReadableError }
  | { status: "done"; action: string; message: string };

export type SetupRunMessage =
  | { kind: "started"; action: string }
  | { kind: "line"; line: string }
  | { kind: "exit"; code: number | null }
  | { kind: "failed"; error: ReadableError };

const PERCENT = 100;
const UNEXPECTED_EXIT: ReadableError = {
  message: "L'installation s'est arrêtée sans résultat.",
  hint: "Analysez à nouveau, puis réessayez.",
  file: null,
};

export function setupRunReducer(run: SetupRun, message: SetupRunMessage): SetupRun {
  if (message.kind === "started") {
    return { status: "running", action: message.action, percent: null, message: "" };
  }
  if (run.status !== "running") {
    return run;
  }
  switch (message.kind) {
    case "failed":
      return { status: "failed", action: run.action, error: message.error };
    case "exit":
      return message.code === 0
        ? { status: "done", action: run.action, message: run.message }
        : { status: "failed", action: run.action, error: UNEXPECTED_EXIT };
    case "line":
      return applyLine(run, message.line);
  }
}

function applyLine(run: Extract<SetupRun, { status: "running" }>, line: string): SetupRun {
  const event = parseEventLine(line);
  switch (event.type) {
    case "progress":
      return {
        ...run,
        percent: Math.round((event.current / event.total) * PERCENT),
        message: event.message,
      };
    case "log":
      return { ...run, message: event.message };
    case "warning":
      return { ...run, message: event.message };
    case "result":
      return { status: "done", action: run.action, message: event.summary };
    case "error":
      return {
        status: "failed",
        action: run.action,
        error: { message: event.message, hint: event.hint, file: event.file },
      };
  }
}

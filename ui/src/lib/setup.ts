import { t } from "../i18n/settings";
import { z } from "zod";
import { CatalogError } from "./catalog";
import { SUCCESS_EXIT_CODE } from "./engine-message";
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
      status: z.enum(["ok", "missing", "optional", "update"]),
      detail: z.string(),
      actions: z.array(setupActionSchema),
      help: z.string().nullable(),
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
  "streamdock.install-plugin",
  "streamdock.install-autocad-plugin",
] as const;
export type EngineSetupAction = (typeof ENGINE_ACTIONS)[number];

const INSTALLS_THIRD_PARTY = new Set(["oda.install", "ollama.install", "model.pull"]);
export const SETUP_TAB_ID = "setup";
export const AI_MODELS_TAB_ID = "ai-models";
export const OPEN_MODELS_ACTION = "models.open";
const OS_LABELS = { windows: "Windows", macos: "macOS", linux: "Linux" } as const;

export function parseSetupReport(rawJson: string): SetupReport {
  const parsed = setupReportSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError(t("setup.invalidReport"));
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
  return `${OS_LABELS[os]} · ${arch} · ${manager ?? t("setup.noPackageManager")}`;
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

export type SetupScope = "setup" | "models";
export type SetupRuns = Record<SetupScope, SetupRun>;
export interface ScopedSetupRunMessage {
  scope: SetupScope;
  message: SetupRunMessage;
}

export const IDLE_SETUP_RUNS: SetupRuns = { setup: { status: "idle" }, models: { status: "idle" } };

export function setupRunsReducer(
  runs: SetupRuns,
  { scope, message }: ScopedSetupRunMessage,
): SetupRuns {
  return { ...runs, [scope]: setupRunReducer(runs[scope], message) };
}

const PERCENT = 100;
function unexpectedExit(): ReadableError {
  return { message: t("setup.unexpectedExit"), hint: t("setup.unexpectedExitHint"), file: null };
}

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
      return message.code === SUCCESS_EXIT_CODE
        ? { status: "done", action: run.action, message: run.message }
        : { status: "failed", action: run.action, error: unexpectedExit() };
    case "line":
      return applyLine(run, message.line);
  }
}

function applyLine(run: Extract<SetupRun, { status: "running" }>, line: string): SetupRun {
  const event = parseEventLine(line);
  if (event === null) {
    return run;
  }
  switch (event.type) {
    case "progress":
      return {
        ...run,
        percent: Math.round((event.current / event.total) * PERCENT),
        message: event.message,
      };
    case "log":
      return { ...run, message: event.message };
    case "table":
      return run;
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

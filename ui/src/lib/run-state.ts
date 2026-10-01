import type { EngineMessage } from "./engine-message";
import { parseEventLine, type EngineEvent, type ProgressEvent } from "./events";

export type RunStatus = "idle" | "running" | "succeeded" | "failed" | "cancelled";
export type LogLevel = "info" | "warning" | "error" | "detail";

export interface LogEntry {
  id: number;
  level: LogLevel;
  message: string;
  file: string | null;
  hint: string | null;
}

export interface RunState {
  status: RunStatus;
  progress: ProgressEvent | null;
  log: LogEntry[];
  summary: string | null;
  outputs: string[];
  cancelRequested: boolean;
}

export type RunAction =
  | { type: "started" }
  | { type: "message"; message: EngineMessage }
  | { type: "cancelRequested" }
  | { type: "bridgeFailed"; message: string };

export const INITIAL_RUN_STATE: RunState = {
  status: "idle",
  progress: null,
  log: [],
  summary: null,
  outputs: [],
  cancelRequested: false,
};

const SUCCESS_EXIT_CODE = 0;

export function runReducer(state: RunState, action: RunAction): RunState {
  switch (action.type) {
    case "started":
      return { ...INITIAL_RUN_STATE, status: "running" };
    case "cancelRequested":
      return { ...state, cancelRequested: true };
    case "bridgeFailed":
      return appendLog({ ...state, status: "failed" }, "error", action.message);
    case "message":
      return applyMessage(state, action.message);
  }
}

export function hasErrors(state: RunState): boolean {
  return state.log.some((entry) => entry.level === "error");
}

function applyMessage(state: RunState, message: EngineMessage): RunState {
  switch (message.kind) {
    case "stdout":
      return applyEvent(state, parseEventLine(message.line));
    case "stderr":
      return appendLog(state, "detail", message.line);
    case "exit":
      return finish(state, message.code);
  }
}

function applyEvent(state: RunState, event: EngineEvent): RunState {
  switch (event.type) {
    case "progress":
      return { ...state, progress: event };
    case "log":
      return appendLog(state, "info", event.message);
    case "warning":
      return appendLog(state, "warning", event.message, event.file);
    case "error":
      return appendLog(state, "error", event.message, event.file, event.hint);
    case "result":
      return { ...state, summary: event.summary, outputs: event.outputs };
  }
}

function finish(state: RunState, exitCode: number | null): RunState {
  if (state.cancelRequested) {
    return appendLog({ ...state, status: "cancelled" }, "warning", "Traitement annulé.");
  }
  if (exitCode === SUCCESS_EXIT_CODE && !hasErrors(state)) {
    return { ...state, status: "succeeded" };
  }
  const failed = { ...state, status: "failed" as const };
  if (hasErrors(state)) {
    return failed;
  }
  return appendLog(
    failed,
    "error",
    `Le moteur s'est arrêté de façon inattendue (code ${String(exitCode)}).`,
  );
}

function appendLog(
  state: RunState,
  level: LogLevel,
  message: string,
  file: string | null = null,
  hint: string | null = null,
): RunState {
  const entry: LogEntry = { id: state.log.length, level, message, file, hint };
  return { ...state, log: [...state.log, entry] };
}

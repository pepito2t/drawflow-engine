import { INITIAL_RUN_STATE, runReducer, type RunAction, type RunState } from "./run-state";

export interface ModuleRunEntry {
  run: RunState;
  runId: string | null;
  unseenOutcome: boolean;
}

export type RunsState = Readonly<Record<string, ModuleRunEntry>>;

export type RunsAction =
  | { type: "run"; moduleId: string; action: RunAction }
  | { type: "runIdAssigned"; moduleId: string; runId: string }
  | { type: "acknowledge"; moduleId: string };

const EMPTY_ENTRY: ModuleRunEntry = { run: INITIAL_RUN_STATE, runId: null, unseenOutcome: false };

export function entryFor(state: RunsState, moduleId: string): ModuleRunEntry {
  return state[moduleId] ?? EMPTY_ENTRY;
}

export function runsReducer(state: RunsState, action: RunsAction): RunsState {
  const entry = entryFor(state, action.moduleId);
  switch (action.type) {
    case "run":
      return { ...state, [action.moduleId]: applyRunAction(entry, action.action) };
    case "runIdAssigned":
      return { ...state, [action.moduleId]: { ...entry, runId: action.runId } };
    case "acknowledge":
      return entry.unseenOutcome
        ? { ...state, [action.moduleId]: { ...entry, unseenOutcome: false } }
        : state;
  }
}

function applyRunAction(entry: ModuleRunEntry, action: RunAction): ModuleRunEntry {
  const run = runReducer(entry.run, action);
  const justFinished = entry.run.status === "running" && run.status !== "running";
  if (action.type === "started") {
    return { run, runId: null, unseenOutcome: false };
  }
  return { ...entry, run, unseenOutcome: entry.unseenOutcome || justFinished };
}

export interface PendingCancellation {
  moduleId: string;
  runId: string;
}

/** Cancellations asked for while the engine was still starting become actionable once the run id arrives. */
export function pendingCancellations(state: RunsState): PendingCancellation[] {
  return Object.entries(state)
    .filter(([, entry]) => entry.run.status === "running" && entry.run.cancelRequested)
    .flatMap(([moduleId, entry]) =>
      entry.runId === null ? [] : [{ moduleId, runId: entry.runId }],
    );
}

export function runningModuleIds(state: RunsState): string[] {
  return Object.entries(state)
    .filter(([, entry]) => entry.run.status === "running")
    .map(([moduleId]) => moduleId);
}

export function overallProgress(state: RunsState): number | null {
  const progresses = runningModuleIds(state)
    .map((moduleId) => entryFor(state, moduleId).run.progress)
    .filter((progress) => progress !== null);
  if (progresses.length === 0) {
    return null;
  }
  const current = progresses.reduce((sum, progress) => sum + progress.current, 0);
  const total = progresses.reduce((sum, progress) => sum + progress.total, 0);
  return current / total;
}

export function visibleRunIds(state: RunsState): string[] {
  return Object.entries(state)
    .filter(([, entry]) => entry.run.status !== "idle")
    .map(([moduleId]) => moduleId);
}

export interface RunsStore {
  getState: () => RunsState;
  dispatch: (action: RunsAction) => void;
  subscribe: (listener: () => void) => () => void;
}

/** Lives outside React so each screen subscribes to the slice it shows, not to every message. */
export function createRunsStore(initial: RunsState = {}): RunsStore {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getState: () => state,
    dispatch: (action) => {
      const next = runsReducer(state, action);
      if (next === state) {
        return;
      }
      state = next;
      for (const listener of listeners) {
        listener();
      }
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

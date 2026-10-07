import { appEventSchema, type AppState, type RunStatus } from "./protocol";

export interface RunView {
  status: RunStatus;
  current: number | null;
  total: number | null;
}

export type Runs = ReadonlyMap<string, RunView>;

const IDLE: RunView = { status: "idle", current: null, total: null };

export function runFor(runs: Runs, moduleId: string): RunView {
  return runs.get(moduleId) ?? IDLE;
}

export function runsFromState(state: AppState): Runs {
  return new Map(
    state.runs.map((run) => [
      run.moduleId,
      { status: run.status, current: run.current, total: run.total },
    ]),
  );
}

/** Applies a Drawflow event; unrelated or unknown events leave the runs unchanged. */
export function applyEvent(runs: Runs, raw: unknown): Runs {
  const parsed = appEventSchema.safeParse(raw);
  if (!parsed.success) {
    return runs;
  }
  const event = parsed.data;
  const next = new Map(runs);
  switch (event.type) {
    case "runStarted":
      next.set(event.moduleId, { status: "running", current: null, total: null });
      return next;
    case "runProgress":
      next.set(event.moduleId, { status: "running", current: event.current, total: event.total });
      return next;
    case "runFinished":
      next.set(event.moduleId, { status: event.outcome, current: null, total: null });
      return next;
    case "presetSaved":
    case "resync":
      return runs;
  }
}

/** Events after which the whole state must be read again from Drawflow. */
export function needsResync(raw: unknown): boolean {
  const parsed = appEventSchema.safeParse(raw);
  return parsed.success && (parsed.data.type === "presetSaved" || parsed.data.type === "resync");
}

/** A finished result stays on the key until it is pressed again. */
export function acknowledge(runs: Runs, moduleId: string): Runs {
  const run = runFor(runs, moduleId);
  if (run.status === "running" || run.status === "idle") {
    return runs;
  }
  const next = new Map(runs);
  next.set(moduleId, IDLE);
  return next;
}

export function runningCount(runs: Runs): number {
  return [...runs.values()].filter((run) => run.status === "running").length;
}

export function progressRatio(run: RunView): number | null {
  return run.current !== null && run.total ? Math.min(run.current / run.total, 1) : null;
}

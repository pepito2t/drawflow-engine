import type {
  EngineMessage,
  EngineMessageHandler,
  InvalidMessageHandler,
} from "../../engine-message";
import type { FormValues } from "../../form-schema";
import type { EngineRequestName } from "../engine";

export interface FakeRun {
  runId: string;
  moduleId: string;
  inputs: FormValues;
  emit: EngineMessageHandler;
  invalid: InvalidMessageHandler;
}

export interface FakeRequest {
  request: EngineRequestName;
  payload: Record<string, unknown>;
}

const EMPTY_SETTINGS = JSON.stringify({ sections: [] });

/** Every run started through the fake bridge, in order; tests drive them with `emit`. */
export const fakeRuns: FakeRun[] = [];
export const cancelledRunIds: string[] = [];
export const fakeRequests: FakeRequest[] = [];

let settingsJson = EMPTY_SETTINGS;
let settingsReads = 0;
const requestResponses = new Map<EngineRequestName, string>();

export function resetFakeEngine(): void {
  fakeRuns.length = 0;
  cancelledRunIds.length = 0;
  fakeRequests.length = 0;
  requestResponses.clear();
  settingsJson = EMPTY_SETTINGS;
  settingsReads = 0;
}

export function setFakeSettings(json: string): void {
  settingsJson = json;
}

export function settingsReadCount(): number {
  return settingsReads;
}

export function respondTo(request: EngineRequestName, json: string): void {
  requestResponses.set(request, json);
}

export function listModules(): Promise<string> {
  return Promise.resolve(JSON.stringify([]));
}

export function getSettings(): Promise<string> {
  settingsReads += 1;
  return Promise.resolve(settingsJson);
}

export function saveSettings(): Promise<string> {
  return Promise.resolve(settingsJson);
}

export function engineRequest(
  request: EngineRequestName,
  payload: Record<string, unknown> = {},
): Promise<string> {
  fakeRequests.push({ request, payload });
  return Promise.resolve(requestResponses.get(request) ?? "[]");
}

export function runModule(
  moduleId: string,
  inputs: FormValues,
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): Promise<string> {
  const runId = `run-${String(fakeRuns.length + 1)}`;
  fakeRuns.push({ runId, moduleId, inputs, emit: onMessage, invalid: onInvalid });
  return Promise.resolve(runId);
}

export function cancelRun(runId: string): Promise<void> {
  cancelledRunIds.push(runId);
  return Promise.resolve();
}

export function describeBridgeError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export const exitMessage = (code: number | null): EngineMessage => ({ kind: "exit", code });

export const engineEvent = (event: Record<string, unknown>): EngineMessage => ({
  kind: "stdout",
  line: JSON.stringify(event),
});

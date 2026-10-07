import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { engineEvent, exitMessage } from "../lib/tauri/__mocks__/engine";
import type { EngineMessage } from "../lib/engine-message";
import { runsReducer, type RunsAction, type RunsState } from "../lib/runs-store";
import { catalogModule, useRecordedEvents } from "../test/providers";
import { NotificationProvider } from "./notification-center";
import { useRunEvents } from "./use-run-events";

const MODULES = [catalogModule("parts")];

const started: RunsAction = { type: "run", moduleId: "parts", action: { type: "started" } };
const received = (message: EngineMessage): RunsAction => ({
  type: "run",
  moduleId: "parts",
  action: { type: "message", message },
});
const progress = (current: number) =>
  received(engineEvent({ type: "progress", current, total: 3, message: "a.dwg" }));

function after(...actions: RunsAction[]): RunsState {
  return actions.reduce(runsReducer, {});
}

function renderRunEvents() {
  return renderHook(
    ({ state }: { state: RunsState }) => {
      useRunEvents(state, MODULES);
      return useRecordedEvents();
    },
    { wrapper: NotificationProvider, initialProps: { state: {} } },
  );
}

describe("useRunEvents", () => {
  it("publishes the start, each new progress step and the outcome of a run", () => {
    const { result, rerender } = renderRunEvents();

    rerender({ state: after(started) });
    rerender({ state: after(started, progress(1)) });
    rerender({
      state: after(started, progress(1), received(engineEvent({ type: "log", message: "x" }))),
    });
    rerender({
      state: after(
        started,
        progress(1),
        received(engineEvent({ type: "result", summary: "3 pièces", outputs: ["out.xlsx"] })),
        received(exitMessage(0)),
      ),
    });

    expect(result.current.map((event) => event.type)).toEqual([
      "runStarted",
      "runProgress",
      "runFinished",
    ]);
    expect(result.current[0]).toEqual({
      type: "runStarted",
      moduleId: "parts",
      moduleName: "Module parts",
    });
    expect(result.current[2]).toMatchObject({
      type: "runFinished",
      outcome: "succeeded",
      message: "3 pièces",
      outputs: ["out.xlsx"],
    });
  });

  it("reports a cancelled run as cancelled", () => {
    const { result, rerender } = renderRunEvents();
    const cancelRequested: RunsAction = {
      type: "run",
      moduleId: "parts",
      action: { type: "cancelRequested" },
    };

    rerender({ state: after(started) });
    rerender({ state: after(started, cancelRequested, received(exitMessage(null))) });

    expect(result.current.at(-1)).toMatchObject({ type: "runFinished", outcome: "cancelled" });
  });

  it("publishes nothing for modules that never ran", () => {
    const { result, rerender } = renderRunEvents();

    rerender({ state: after({ type: "acknowledge", moduleId: "parts" }) });

    expect(result.current).toEqual([]);
  });
});

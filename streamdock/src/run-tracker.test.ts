import { describe, expect, it } from "vitest";
import {
  acknowledge,
  applyEvent,
  needsResync,
  progressRatio,
  runFor,
  runningCount,
  runsFromState,
  type Runs,
} from "./run-tracker";

const apply = (events: object[]): Runs =>
  events.reduce<Runs>((runs, event) => applyEvent(runs, event), new Map());

describe("run tracker", () => {
  it("follows a run from start to result", () => {
    const runs = apply([
      { type: "runStarted", moduleId: "dwg-parts" },
      { type: "runProgress", moduleId: "dwg-parts", current: 2, total: 8 },
    ]);

    expect(progressRatio(runFor(runs, "dwg-parts"))).toBe(0.25);
    expect(runningCount(runs)).toBe(1);
    expect(
      runFor(
        applyEvent(runs, { type: "runFinished", moduleId: "dwg-parts", outcome: "failed" }),
        "dwg-parts",
      ).status,
    ).toBe("failed");
  });

  it("keeps the result until the key is pressed", () => {
    const runs = apply([{ type: "runFinished", moduleId: "a", outcome: "succeeded" }]);

    expect(runFor(acknowledge(runs, "a"), "a").status).toBe("idle");
  });

  it("does not reset a running feature on press", () => {
    const runs = apply([{ type: "runStarted", moduleId: "a" }]);

    expect(acknowledge(runs, "a")).toBe(runs);
  });

  it("asks for a full reload on presetSaved and resync only", () => {
    expect(needsResync({ type: "resync" })).toBe(true);
    expect(needsResync({ type: "presetSaved" })).toBe(true);
    expect(needsResync({ type: "runStarted", moduleId: "a" })).toBe(false);
    expect(needsResync("resync")).toBe(false);
    expect(applyEvent(new Map(), { type: "resync" }).size).toBe(0);
  });

  it("ignores unknown events", () => {
    const runs = apply([{ type: "settingsSaved" }]);

    expect(runs.size).toBe(0);
  });

  it("seeds runs from the app state", () => {
    const runs = runsFromState({
      modules: [],
      presets: [],
      runs: [{ moduleId: "a", status: "running", current: 1, total: 2 }],
    });

    expect(runFor(runs, "a")).toEqual({ status: "running", current: 1, total: 2 });
  });
});

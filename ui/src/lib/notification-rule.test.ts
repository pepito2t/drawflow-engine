import { describe, expect, it } from "vitest";
import { describeOutcome, shouldNotify } from "./notification-rule";
import { INITIAL_RUN_STATE, type RunState } from "./run-state";

describe("shouldNotify", () => {
  it("notifies long runs even when the window is focused", () => {
    expect(shouldNotify(12_000, 10, true)).toBe(true);
  });

  it("stays silent for short runs in a focused window", () => {
    expect(shouldNotify(3_000, 10, true)).toBe(false);
  });

  it("always notifies when the window is in the background", () => {
    expect(shouldNotify(500, 10, false)).toBe(true);
  });

  it("notifies every run when the threshold is zero", () => {
    expect(shouldNotify(0, 0, true)).toBe(true);
  });
});

describe("describeOutcome", () => {
  const finished = (overrides: Partial<RunState>): RunState => ({
    ...INITIAL_RUN_STATE,
    ...overrides,
  });

  it("uses the summary for successes", () => {
    expect(
      describeOutcome("Liste de pièces", finished({ status: "succeeded", summary: "12 pièces" })),
    ).toEqual({
      title: "Liste de pièces terminé",
      body: "12 pièces",
    });
  });

  it("uses the first error for failures", () => {
    const run = finished({
      status: "failed",
      log: [
        {
          id: 0,
          level: "error",
          message: "ODA introuvable",
          file: null,
          location: null,
          hint: null,
        },
      ],
    });

    expect(describeOutcome("Liste de pièces", run)?.body).toBe("ODA introuvable");
  });

  it("does not notify cancelled runs", () => {
    expect(describeOutcome("Rapport", finished({ status: "cancelled" }))).toBeNull();
  });
});

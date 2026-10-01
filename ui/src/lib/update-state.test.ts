import { describe, expect, it } from "vitest";
import { describeUpdate, updateReducer, type UpdateAction, type UpdateState } from "./update-state";

const reduce = (state: UpdateState, actions: UpdateAction[]) =>
  actions.reduce(updateReducer, state);

describe("updateReducer", () => {
  it("goes from available to installing through download progress", () => {
    const downloading = reduce({ status: "available", version: "1.2.0" }, [
      { type: "downloadStarted" },
      { type: "progressed", downloaded: 50, total: 200 },
    ]);

    expect(downloading).toEqual({ status: "downloading", version: "1.2.0", progress: 0.25 });
    expect(updateReducer(downloading, { type: "downloaded" })).toEqual({
      status: "installing",
      version: "1.2.0",
    });
  });

  it("keeps an unknown size as indeterminate progress", () => {
    const state = reduce({ status: "available", version: "1.2.0" }, [
      { type: "downloadStarted" },
      { type: "progressed", downloaded: 50, total: null },
    ]);

    expect(state).toMatchObject({ progress: null });
  });

  it("ignores downloads when no update is available", () => {
    expect(updateReducer({ status: "upToDate" }, { type: "downloadStarted" })).toEqual({
      status: "upToDate",
    });
  });

  it("applies the startup check result only once", () => {
    const checked = updateReducer(
      { status: "checking" },
      { type: "checked", state: { status: "upToDate" } },
    );

    expect(checked).toEqual({ status: "upToDate" });
    expect(updateReducer(checked, { type: "checked", state: { status: "unconfigured" } })).toEqual(
      checked,
    );
  });

  it("reports failures", () => {
    expect(updateReducer({ status: "upToDate" }, { type: "failed", message: "réseau" })).toEqual({
      status: "error",
      message: "réseau",
    });
  });
});

describe("describeUpdate", () => {
  it.each<[UpdateState, string]>([
    [{ status: "unconfigured" }, "Mises à jour : non configurées"],
    [{ status: "upToDate" }, "À jour"],
    [{ status: "available", version: "1.2.0" }, "Version 1.2.0 disponible"],
    [{ status: "downloading", version: "1.2.0", progress: 0.4 }, "Téléchargement 40 %"],
    [{ status: "installing", version: "1.2.0" }, "Installation de 1.2.0…"],
  ])("labels %o", (state, label) => {
    expect(describeUpdate(state)).toBe(label);
  });
});

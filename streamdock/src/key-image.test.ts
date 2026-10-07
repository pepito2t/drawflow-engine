import { describe, expect, it } from "vitest";
import { faceFor, renderKey } from "./key-image";

const decode = (image: string) =>
  decodeURIComponent(image.replace("data:image/svg+xml;charset=utf8,", ""));

describe("key faces", () => {
  it("shows offline and locked states before anything else", () => {
    const running = { status: "running" as const, current: 1, total: 2 };

    expect(faceFor("offline", "Tour B", running).tone).toBe("offline");
    expect(faceFor("locked", "Tour B", running)).toMatchObject({
      tone: "locked",
      detail: "Verrouillé",
    });
    expect(faceFor("refused", "Tour B", running)).toMatchObject({
      tone: "refused",
      detail: "Jeton invalide",
    });
  });

  it("shows live progress while running", () => {
    expect(faceFor("ready", "Tour B", { status: "running", current: 3, total: 4 })).toEqual({
      tone: "running",
      label: "Tour B",
      detail: "75 %",
      progress: 0.75,
    });
  });

  it("shows green or red results", () => {
    expect(faceFor("ready", "A", { status: "succeeded", current: null, total: null }).tone).toBe(
      "succeeded",
    );
    expect(faceFor("ready", "A", { status: "failed", current: null, total: null }).tone).toBe(
      "failed",
    );
  });

  it("says that a run was cancelled until the key is pressed again", () => {
    expect(faceFor("ready", "A", { status: "cancelled", current: null, total: null })).toEqual({
      tone: "idle",
      label: "A",
      detail: "Annulé",
      progress: null,
    });
  });

  it("renders an escaped svg with a progress bar", () => {
    const svg = decode(
      renderKey({ tone: "running", label: "R&D <Tour>", detail: "50 %", progress: 0.5 }),
    );

    expect(svg).toContain("R&amp;D");
    expect(svg).toContain("&lt;Tour&gt;");
    expect(svg).toContain('width="56"');
  });

  it("wraps a long detail on two lines and ends it with an ellipsis", () => {
    const svg = decode(
      renderKey({
        tone: "failed",
        label: "Tour B",
        detail: "Un traitement est déjà en cours pour cette fonctionnalité",
        progress: null,
      }),
    );

    expect(svg.match(/class="detail"/g)).toHaveLength(2);
    expect(svg).toContain("est déjà en…</text>");
    expect(svg.match(/class="label"/g)).toHaveLength(1);
  });

  it("wraps long labels on two lines at most", () => {
    const svg = decode(
      renderKey({
        tone: "idle",
        label: "Liste de pièces façade nord ouest",
        detail: null,
        progress: null,
      }),
    );

    expect(svg.match(/class="label"/g)).toHaveLength(2);
  });
});

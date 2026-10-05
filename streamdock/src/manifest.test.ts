import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { BEHAVIORS } from "./behaviors";

const PLUGIN_FOLDER = join(import.meta.dirname, "..", "ch.drawflow.sdPlugin");
const UUID_PATTERN = /^[a-z0-9.-]+$/;

interface Manifest {
  Version: string;
  SDKVersion: number;
  CodePathWin: string;
  Icon: string;
  CategoryIcon: string;
  Nodejs: { Version: string };
  Actions: {
    UUID: string;
    Icon: string;
    PropertyInspectorPath?: string;
    States: { Image: string }[];
  }[];
}

const manifest = JSON.parse(readFileSync(join(PLUGIN_FOLDER, "manifest.json"), "utf8")) as Manifest;

describe("Stream Dock manifest", () => {
  it("uses the Stream Dock SDK with its built-in Node", () => {
    expect(manifest.SDKVersion).toBe(1);
    expect(manifest.CodePathWin).toBe("bin/plugin.js");
    expect(manifest.Nodejs.Version).toBe("20");
    expect(manifest.Version).toMatch(/^\d+\.\d+\.\d+$/);
  });

  it("declares exactly the keys the plugin knows how to drive", () => {
    expect(manifest.Actions.map((action) => action.UUID).sort()).toEqual(
      Object.keys(BEHAVIORS).sort(),
    );
    for (const action of manifest.Actions) {
      expect(action.UUID).toMatch(UUID_PATTERN);
    }
  });

  it("only references PNG images and pages that exist", () => {
    const files = [
      manifest.Icon,
      manifest.CategoryIcon,
      ...manifest.Actions.flatMap((action) => [
        action.Icon,
        ...action.States.map((state) => state.Image),
        ...(action.PropertyInspectorPath ? [action.PropertyInspectorPath] : []),
      ]),
    ];
    for (const file of files) {
      expect(existsSync(join(PLUGIN_FOLDER, file)), file).toBe(true);
    }
    expect(
      files.filter((file) => file.startsWith("imgs/")).every((file) => file.endsWith(".png")),
    ).toBe(true);
  });
});

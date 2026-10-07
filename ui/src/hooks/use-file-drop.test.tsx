import { act, render, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { dropFiles, dropListenerCount } from "../lib/tauri/__mocks__/drag-drop";
import { dropFieldProps, useFileDrop } from "./use-file-drop";

vi.mock("../lib/tauri/drag-drop");

const DROP_X = 10;
const DROP_Y = 20;

function renderDropTarget(moduleId: string, fieldName: string): HTMLElement {
  const { container } = render(<div {...dropFieldProps(moduleId, fieldName)} />);
  const target = container.firstElementChild;
  if (!(target instanceof HTMLElement)) {
    throw new Error("Zone de dépôt absente.");
  }
  return target;
}

describe("useFileDrop", () => {
  let underPointer: Element | null = null;

  beforeEach(() => {
    document.elementFromPoint = () => underPointer;
  });

  afterEach(() => {
    underPointer = null;
  });

  it("hands the dropped paths to the field under the pointer of its own module", async () => {
    const drops: [string, string[]][] = [];
    renderHook(() => {
      useFileDrop("parts", (field, paths) => drops.push([field, paths]));
    });
    await act(async () => {
      await Promise.resolve();
    });
    underPointer = renderDropTarget("parts", "drawings");

    dropFiles({ paths: ["C:\\plans\\a.dwg"], x: DROP_X, y: DROP_Y });

    expect(drops).toEqual([["drawings", ["C:\\plans\\a.dwg"]]]);
  });

  it("ignores drops on another module's field with the same name", async () => {
    const drops: string[] = [];
    renderHook(() => {
      useFileDrop("parts", (field) => drops.push(field));
    });
    await act(async () => {
      await Promise.resolve();
    });
    underPointer = renderDropTarget("diff", "drawings");

    dropFiles({ paths: ["a.dwg"], x: DROP_X, y: DROP_Y });

    expect(drops).toEqual([]);
  });

  it("stops listening once unmounted", async () => {
    const { unmount } = renderHook(() => {
      useFileDrop("parts", () => undefined);
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(dropListenerCount()).toBe(1);

    unmount();

    expect(dropListenerCount()).toBe(0);
  });
});

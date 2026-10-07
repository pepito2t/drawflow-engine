import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AppEvent } from "../lib/app-events";
import { NotificationProvider, useNotificationCenter } from "./notification-center";

function renderCenter() {
  return renderHook(() => useNotificationCenter(), { wrapper: NotificationProvider });
}

describe("notification center", () => {
  it("delivers each published event to every subscriber until it unsubscribes", () => {
    const { result } = renderCenter();
    const first: AppEvent[] = [];
    const second: AppEvent[] = [];
    const stopFirst = result.current.subscribe((event) => first.push(event));
    result.current.subscribe((event) => second.push(event));

    act(() => {
      result.current.publish({ type: "settingsSaved" });
    });
    stopFirst();
    act(() => {
      result.current.publish({ type: "updateDeferred" });
    });

    expect(first).toEqual([{ type: "settingsSaved" }]);
    expect(second).toEqual([{ type: "settingsSaved" }, { type: "updateDeferred" }]);
  });

  it("shows a toast for notable events and dismisses it on request", () => {
    const { result } = renderCenter();

    act(() => {
      result.current.publish({ type: "settingsSaved" });
    });
    const [toast] = result.current.toasts;
    expect(toast?.title).toBe("Paramètres enregistrés");

    act(() => {
      if (toast) result.current.dismiss(toast.id);
    });
    expect(result.current.toasts).toEqual([]);
  });

  it("refuses to be used outside its provider", () => {
    expect(() => renderHook(() => useNotificationCenter())).toThrow(/NotificationProvider/);
  });
});

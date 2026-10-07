import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { HistoryPanel } from "../components/HistoryPanel";
import { TodayPanel } from "../components/TodayPanel";
import { fakeRequests, resetFakeEngine, respondTo } from "../lib/tauri/__mocks__/engine";
import { TestProviders } from "../test/providers";
import { HistoryProvider } from "./history-context";
import { useNotificationCenter } from "./notification-center";

vi.mock("../lib/tauri/engine");
vi.mock("../lib/tauri/window");

const ENTRY = {
  id: "1",
  started_at: "2026-10-07T08:00:00Z",
  module: "parts",
  module_name: "Liste de pièces",
  inputs: {},
  status: "succeeded",
  summary: "12 pièces",
  outputs: [],
  warnings: [],
  error: null,
  duration_ms: 1200,
};

function RunFinishedTrigger() {
  const { publish } = useNotificationCenter();
  return (
    <button
      type="button"
      onClick={() => {
        publish({
          type: "runFinished",
          moduleId: "parts",
          moduleName: "Liste de pièces",
          outcome: "succeeded",
          message: "ok",
          durationMs: 1,
          outputs: [],
        });
      }}
    >
      Terminer
    </button>
  );
}

const historyReads = () => fakeRequests.filter(({ request }) => request === "history.list").length;

describe("shared history", () => {
  beforeEach(() => {
    resetFakeEngine();
    respondTo("history.list", JSON.stringify({ entries: [ENTRY] }));
  });

  it("feeds the Today and History panels from one read, refreshed once per finished run", async () => {
    await act(async () => {
      render(
        <TestProviders>
          <HistoryProvider>
            <RunFinishedTrigger />
            <TodayPanel modules={[]} />
            <HistoryPanel />
          </HistoryProvider>
        </TestProviders>,
      );
      await Promise.resolve();
    });
    expect(screen.getAllByText("12 pièces")).toHaveLength(2);
    expect(historyReads()).toBe(1);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Terminer" }));
      await Promise.resolve();
    });
    expect(screen.getAllByText("12 pièces")).toHaveLength(2);

    expect(historyReads()).toBe(2);
  });
});

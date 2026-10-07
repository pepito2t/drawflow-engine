import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { currentLanguage, setLanguage } from "../i18n";
import type { AppEvent } from "../lib/app-events";
import { resetFakeEngine, setFakeSettings, settingsReadCount } from "../lib/tauri/__mocks__/engine";
import { resetFakeNotifications, sentNotifications } from "../lib/tauri/__mocks__/notification";
import { NotificationProvider, useNotificationCenter } from "./notification-center";
import { SettingsFeedProvider } from "./settings-feed";
import { useLanguageSync } from "./use-language-sync";
import { useSystemNotifications } from "./use-system-notifications";

vi.mock("../lib/tauri/engine");
vi.mock("../lib/tauri/notification");

const THRESHOLD_SECONDS = 30;
const SHORT_RUN_MS = 5_000;
const LONG_RUN_MS = 60_000;

function generalSettings(language: string): string {
  return JSON.stringify({
    sections: [
      {
        id: "general",
        title: "Général",
        schema: {
          properties: {
            language: { title: "Langue", "x-ui": "enum", enum: ["fr", "en"] },
            notification_threshold_seconds: { title: "Seuil", "x-ui": "number" },
          },
        },
        values: { language, notification_threshold_seconds: THRESHOLD_SECONDS },
        error: null,
      },
    ],
  });
}

function Providers({ children }: { children: ReactNode }) {
  return (
    <NotificationProvider>
      <SettingsFeedProvider>{children}</SettingsFeedProvider>
    </NotificationProvider>
  );
}

async function renderSettingsConsumers() {
  const rendered = renderHook(
    () => {
      useLanguageSync();
      useSystemNotifications();
      return useNotificationCenter();
    },
    { wrapper: Providers },
  );
  await settle();
  return rendered;
}

async function settle(): Promise<void> {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

function finishedRun(durationMs: number): AppEvent {
  return {
    type: "runFinished",
    moduleId: "parts",
    moduleName: "Liste de pièces",
    outcome: "succeeded",
    message: "12 pièces",
    durationMs,
    outputs: [],
  };
}

describe("settings feed", () => {
  beforeEach(() => {
    resetFakeEngine();
    resetFakeNotifications();
    setFakeSettings(generalSettings("fr"));
  });

  afterEach(() => {
    setLanguage("fr");
  });

  it("reads the settings once at start for the language and the notification threshold", async () => {
    await renderSettingsConsumers();

    expect(settingsReadCount()).toBe(1);
    expect(currentLanguage()).toBe("fr");
  });

  it("reads the settings once per save, whatever the number of screens that use them", async () => {
    const { result } = await renderSettingsConsumers();
    setFakeSettings(generalSettings("en"));

    act(() => {
      result.current.publish({ type: "settingsSaved" });
    });
    await settle();

    expect(settingsReadCount()).toBe(2);
    expect(currentLanguage()).toBe("en");
  });

  it("notifies a finished run with the threshold from that same read, without reading again", async () => {
    const { result } = await renderSettingsConsumers();

    act(() => {
      result.current.publish(finishedRun(SHORT_RUN_MS));
      result.current.publish(finishedRun(LONG_RUN_MS));
    });
    await settle();

    expect(settingsReadCount()).toBe(1);
    expect(sentNotifications).toEqual([
      { title: expect.stringContaining("Liste de pièces") as string, body: "12 pièces" },
    ]);
  });
});

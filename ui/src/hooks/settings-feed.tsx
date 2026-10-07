import { createContext, use, useEffect, useState, type ReactNode } from "react";
import { getSettings } from "../lib/tauri/engine";
import { useNotificationCenter } from "./notification-center";

type SettingsListener = (rawSettings: string) => void;

interface SettingsFeed {
  /** The last settings read, or null before the first read completes. */
  latest: () => string | null;
  subscribe: (listener: SettingsListener) => () => void;
}

interface WritableSettingsFeed extends SettingsFeed {
  publish: (rawSettings: string) => void;
}

const SettingsFeedContext = createContext<SettingsFeed | null>(null);

function createSettingsFeed(): WritableSettingsFeed {
  let latest: string | null = null;
  const listeners = new Set<SettingsListener>();
  return {
    latest: () => latest,
    publish: (rawSettings) => {
      latest = rawSettings;
      for (const listener of listeners) {
        listener(rawSettings);
      }
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

/** Reads the settings once at start and once per save, for every screen that depends on them. */
export function SettingsFeedProvider({ children }: { children: ReactNode }) {
  const [feed] = useState(createSettingsFeed);
  const { subscribe } = useNotificationCenter();
  useEffect(() => {
    let latestRead = 0;
    const read = () => {
      latestRead += 1;
      const thisRead = latestRead;
      getSettings()
        .then((rawSettings) => {
          // Two quick saves may answer out of order; only the newest read is current.
          if (thisRead === latestRead) {
            feed.publish(rawSettings);
          }
        })
        .catch((error: unknown) => {
          console.error("Paramètres non lus :", error);
        });
    };
    read();
    return subscribe((event) => {
      if (event.type === "settingsSaved") {
        read();
      }
    });
  }, [feed, subscribe]);
  return <SettingsFeedContext value={feed}>{children}</SettingsFeedContext>;
}

export function useSettingsFeed(): SettingsFeed {
  const feed = use(SettingsFeedContext);
  if (feed === null) {
    throw new Error("useSettingsFeed doit être utilisé dans un SettingsFeedProvider.");
  }
  return feed;
}

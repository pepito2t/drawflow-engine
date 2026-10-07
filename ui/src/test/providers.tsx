import { useEffect, useState, type ReactNode } from "react";
import { CommandProvider } from "../hooks/command-registry";
import { NotificationProvider, useNotificationCenter } from "../hooks/notification-center";
import { PresetsProvider } from "../hooks/presets-context";
import { RunsProvider } from "../hooks/runs-context";
import type { AppEvent } from "../lib/app-events";
import type { CatalogModule } from "../lib/catalog";
import type { FieldDescriptor } from "../lib/form-schema";
import type { Preset } from "../lib/presets";

export function TestProviders({
  children,
  presets = [],
}: {
  children: ReactNode;
  presets?: Preset[];
}) {
  return (
    <RunsProvider>
      <NotificationProvider>
        <CommandProvider>
          <PresetsProvider initialPresets={presets}>{children}</PresetsProvider>
        </CommandProvider>
      </NotificationProvider>
    </RunsProvider>
  );
}

export function textField(name: string, label: string, required = true): FieldDescriptor {
  return {
    name,
    label,
    description: null,
    kind: "text",
    required,
    options: [],
    defaultValue: "",
    mappingLabels: null,
  };
}

export function catalogModule(
  id: string,
  fields: FieldDescriptor[] = [textField("name", "Nom")],
): CatalogModule {
  return {
    manifest: {
      id,
      name: `Module ${id}`,
      description: `Description ${id}`,
      version: "1.0.0",
      order: 0,
      instructions: [],
      icon: "module",
    },
    fields,
  };
}

/** Collects every event published on the notification center, in order. */
export function useRecordedEvents(): AppEvent[] {
  const { subscribe } = useNotificationCenter();
  const [events] = useState<AppEvent[]>(() => []);
  useEffect(
    () =>
      subscribe((event) => {
        events.push(event);
      }),
    [subscribe, events],
  );
  return events;
}

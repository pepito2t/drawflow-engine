import { createContext, use, useCallback, useMemo, useState, type ReactNode } from "react";
import type { FormValues } from "../lib/form-schema";
import { parsePresets, type Preset } from "../lib/presets";
import { engineRequest } from "../lib/tauri/engine";

interface PresetsStore {
  presets: Preset[];
  save: (moduleId: string, name: string, inputs: FormValues, presetId?: string) => Promise<void>;
  remove: (presetId: string) => Promise<void>;
  reload: () => Promise<void>;
}

const PresetsContext = createContext<PresetsStore | null>(null);

export function loadPresets(): Promise<Preset[]> {
  return engineRequest("presets.list").then(parsePresets);
}

export function PresetsProvider({
  initialPresets,
  children,
}: {
  initialPresets: Preset[];
  children: ReactNode;
}) {
  const [presets, setPresets] = useState(initialPresets);

  const save = useCallback(
    async (moduleId: string, name: string, inputs: FormValues, presetId?: string) => {
      const payload = { id: presetId ?? null, name, module: moduleId, inputs };
      setPresets(parsePresets(await engineRequest("presets.save", payload)));
    },
    [],
  );

  const remove = useCallback(async (presetId: string) => {
    setPresets(parsePresets(await engineRequest("presets.remove", { id: presetId })));
  }, []);

  const reload = useCallback(async () => {
    setPresets(await loadPresets());
  }, []);

  const store = useMemo(() => ({ presets, save, remove, reload }), [presets, save, remove, reload]);
  return <PresetsContext value={store}>{children}</PresetsContext>;
}

export function usePresets(): PresetsStore {
  const store = use(PresetsContext);
  if (store === null) {
    throw new Error("usePresets doit être utilisé dans un PresetsProvider.");
  }
  return store;
}

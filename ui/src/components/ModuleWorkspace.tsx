import { useCallback, useState } from "react";
import { useFieldDrop } from "../hooks/use-field-drop";
import { useModuleRun } from "../hooks/use-module-run";
import type { CatalogModule } from "../lib/catalog";
import { initialValues, toEngineInputs, type FormValue } from "../lib/form-schema";
import { presetFormValues } from "../lib/presets";
import { ModuleForm } from "./ModuleForm";
import { ModuleInstructions } from "./ModuleInstructions";
import { PresetBar } from "./PresetBar";
import { RunPanel } from "./RunPanel";

interface ModuleWorkspaceProps {
  module: CatalogModule;
}

export function ModuleWorkspace({ module }: ModuleWorkspaceProps) {
  const { manifest, fields } = module;
  const [values, setValues] = useState(() => initialValues(fields));
  const { state, start, cancel } = useModuleRun(manifest.id);
  const isRunning = state.status === "running";

  const setValue = useCallback((name: string, value: FormValue) => {
    setValues((current) => ({ ...current, [name]: value }));
  }, []);
  useFieldDrop(manifest.id, fields, setValues, isRunning);

  return (
    <section className="module-workspace">
      <header>
        <h1>{manifest.name}</h1>
        <p>{manifest.description}</p>
      </header>
      <ModuleInstructions steps={manifest.instructions} />
      <PresetBar
        moduleId={manifest.id}
        disabled={isRunning}
        currentInputs={() => toEngineInputs(fields, values)}
        onLoad={(preset) => {
          setValues(presetFormValues(preset, fields));
        }}
      />
      <ModuleForm
        moduleId={manifest.id}
        fields={fields}
        values={values}
        disabled={isRunning}
        onChange={setValue}
      />
      <RunPanel
        state={state}
        onStart={() => {
          start(toEngineInputs(fields, values));
        }}
        onCancel={cancel}
      />
    </section>
  );
}

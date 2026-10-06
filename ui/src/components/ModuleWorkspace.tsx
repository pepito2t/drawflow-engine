import { useCallback, useEffect, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { usePresets } from "../hooks/presets-context";
import { useFieldDrop } from "../hooks/use-field-drop";
import { useModuleRun } from "../hooks/use-module-run";
import type { CatalogModule } from "../lib/catalog";
import { initialValues, missingRequired, toEngineInputs, type FormValue } from "../lib/form-schema";
import { formValuesFrom, presetFormValues } from "../lib/presets";
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

  const { subscribe, publish } = useNotificationCenter();
  const { presets } = usePresets();
  useEffect(
    () =>
      subscribe((event) => {
        if (event.type !== "presetRunRequested" && event.type !== "featureRunRequested") {
          return;
        }
        if (event.moduleId !== manifest.id) {
          return;
        }
        const inputs =
          event.type === "featureRunRequested"
            ? event.inputs
            : presets.find((candidate) => candidate.id === event.presetId)?.inputs;
        if (inputs) {
          const requested = formValuesFrom(inputs, fields);
          setValues(requested);
          const missing = missingRequired(fields, requested);
          if (missing.length > 0) {
            publish({
              type: "featureRunIncomplete",
              moduleId: manifest.id,
              moduleName: manifest.name,
              missing,
            });
            return;
          }
          start(toEngineInputs(fields, requested));
        }
      }),
    [subscribe, publish, presets, fields, manifest.id, manifest.name, start],
  );

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

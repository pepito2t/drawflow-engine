import { useCallback, useEffect, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { usePresets } from "../hooks/presets-context";
import { useFieldDrop } from "../hooks/use-field-drop";
import { useModuleRun } from "../hooks/use-module-run";
import type { CatalogModule } from "../lib/catalog";
import type { AppEvent } from "../lib/app-events";
import {
  initialValues,
  missingRequired,
  toEngineInputs,
  type FieldDescriptor,
  type FormValue,
  type FormValues,
} from "../lib/form-schema";
import { formValuesFrom, presetFormValues, type Preset } from "../lib/presets";
import { ModuleForm } from "./ModuleForm";
import { ModuleInstructions } from "./ModuleInstructions";
import { PresetBar } from "./PresetBar";
import { RunPanel } from "./RunPanel";

/** The form values a run request for this module asks for: given inputs, a preset's, or the form as it stands. */
function requestedValues(
  event: AppEvent,
  moduleId: string,
  presets: Preset[],
  fields: FieldDescriptor[],
  current: FormValues,
): FormValues | null {
  if (!("moduleId" in event) || event.moduleId !== moduleId) {
    return null;
  }
  switch (event.type) {
    case "featureRunRequested":
      return formValuesFrom(event.inputs, fields);
    case "presetRunRequested": {
      const preset = presets.find((candidate) => candidate.id === event.presetId);
      return preset ? formValuesFrom(preset.inputs, fields) : null;
    }
    case "formRunRequested":
      return current;
    default:
      return null;
  }
}

/** Modules that can show their table first expose this boolean input. */
const PREVIEW_FIELD = "preview";

interface ModuleWorkspaceProps {
  module: CatalogModule;
}

export function ModuleWorkspace({ module }: ModuleWorkspaceProps) {
  const { manifest, fields } = module;
  const [values, setValues] = useState(() => initialValues(fields));
  const { state, start, cancel } = useModuleRun(manifest.id);
  const isRunning = state.status === "running";
  const missingFields = missingRequired(fields, values);

  const setValue = useCallback((name: string, value: FormValue) => {
    setValues((current) => ({ ...current, [name]: value }));
  }, []);
  useFieldDrop(manifest.id, fields, setValues, isRunning);

  const { subscribe, publish } = useNotificationCenter();
  const { presets } = usePresets();
  useEffect(
    () =>
      subscribe((event) => {
        const requested = requestedValues(event, manifest.id, presets, fields, values);
        if (!requested) {
          return;
        }
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
      }),
    [subscribe, publish, presets, fields, values, manifest.id, manifest.name, start],
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
        missingFields={missingFields}
        onStart={() => {
          start(toEngineInputs(fields, values));
        }}
        onExport={() => {
          start(toEngineInputs(fields, { ...values, [PREVIEW_FIELD]: false }));
        }}
        onCancel={cancel}
      />
    </section>
  );
}

import { useCallback, useState } from "react";
import { useFileDrop } from "../hooks/use-file-drop";
import { useModuleRun } from "../hooks/use-module-run";
import type { CatalogModule } from "../lib/catalog";
import {
  initialValues,
  mergeDroppedPaths,
  toEngineInputs,
  type FormValue,
} from "../lib/form-schema";
import { ModuleForm } from "./ModuleForm";
import { ModuleInstructions } from "./ModuleInstructions";
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

  const handleDrop = useCallback(
    (fieldName: string, paths: string[]) => {
      const field = fields.find((candidate) => candidate.name === fieldName);
      if (field && !isRunning) {
        setValues((current) => ({
          ...current,
          [fieldName]: mergeDroppedPaths(field.kind, current[fieldName] ?? "", paths),
        }));
      }
    },
    [fields, isRunning],
  );
  useFileDrop(manifest.id, handleDrop);

  return (
    <section className="module-workspace">
      <header>
        <h1>{manifest.name}</h1>
        <p>{manifest.description}</p>
      </header>
      <ModuleInstructions steps={manifest.instructions} />
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

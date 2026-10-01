import { useCallback, type Dispatch, type SetStateAction } from "react";
import { mergeDroppedPaths, type FieldDescriptor, type FormValues } from "../lib/form-schema";
import { useFileDrop } from "./use-file-drop";

export function useFieldDrop(
  namespace: string,
  fields: FieldDescriptor[],
  setValues: Dispatch<SetStateAction<FormValues>>,
  disabled: boolean,
): void {
  const handleDrop = useCallback(
    (fieldName: string, paths: string[]) => {
      const field = fields.find((candidate) => candidate.name === fieldName);
      if (!field || disabled) {
        return;
      }
      setValues((current) => ({
        ...current,
        [fieldName]: mergeDroppedPaths(field.kind, current[fieldName] ?? "", paths),
      }));
    },
    [fields, disabled, setValues],
  );
  useFileDrop(namespace, handleDrop);
}

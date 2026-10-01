import { dropFieldProps } from "../hooks/use-file-drop";
import {
  isFolderKind,
  isMultipleKind,
  mergeDroppedPaths,
  type FieldDescriptor,
  type FormValue,
} from "../lib/form-schema";
import { pickPaths } from "../lib/tauri/dialog";

interface PathFieldProps {
  moduleId: string;
  field: FieldDescriptor;
  value: FormValue;
  disabled: boolean;
  onChange: (value: FormValue) => void;
}

export function PathField({ moduleId, field, value, disabled, onChange }: PathFieldProps) {
  const paths = toPathList(value);
  const multiple = isMultipleKind(field.kind);

  const browse = () => {
    pickPaths({ directory: isFolderKind(field.kind), multiple, title: field.label })
      .then((selected) => {
        if (selected.length > 0) {
          onChange(mergeDroppedPaths(field.kind, value, selected));
        }
      })
      .catch((error: unknown) => {
        console.error("Sélection de fichier impossible :", error);
      });
  };

  return (
    <div className="path-field" {...dropFieldProps(moduleId, field.name)}>
      <ul id={field.name} className="path-list">
        {paths.length === 0 && <li className="placeholder">Glisser-déposer ici ou Parcourir…</li>}
        {paths.map((path) => (
          <li key={path} title={path}>
            {path}
          </li>
        ))}
      </ul>
      <div className="path-actions">
        <button type="button" disabled={disabled} onClick={browse}>
          Parcourir
        </button>
        {paths.length > 0 && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              onChange(multiple ? [] : "");
            }}
          >
            Effacer
          </button>
        )}
      </div>
    </div>
  );
}

function toPathList(value: FormValue): string[] {
  if (Array.isArray(value)) {
    return value;
  }
  return typeof value === "string" && value !== "" ? [value] : [];
}

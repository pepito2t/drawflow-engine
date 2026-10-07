import { t } from "../i18n/shell";
import { dropFieldProps } from "../hooks/use-file-drop";
import {
  fieldInputId,
  isFolderKind,
  isMultipleKind,
  mergeDroppedPaths,
  toPathList,
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
      <ul id={fieldInputId(moduleId, field.name)} className="path-list">
        {paths.length === 0 && <li className="placeholder">{t("pathField.placeholder")}</li>}
        {paths.map((path) => (
          <li key={path} title={path}>
            {path}
          </li>
        ))}
      </ul>
      <div className="path-actions">
        <button type="button" disabled={disabled} onClick={browse}>
          {t("pathField.browse")}
        </button>
        {paths.length > 0 && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              onChange(multiple ? [] : "");
            }}
          >
            {t("pathField.clear")}
          </button>
        )}
      </div>
    </div>
  );
}

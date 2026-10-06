import { t } from "../i18n/shell";
import {
  toMappingRows,
  type FieldDescriptor,
  type FormValue,
  type MappingRow,
} from "../lib/form-schema";
import { CloseIcon } from "./icons";

interface MappingFieldProps {
  field: FieldDescriptor;
  value: FormValue;
  disabled: boolean;
  onChange: (value: FormValue) => void;
}

const EMPTY_ROW: MappingRow = { key: "", value: "" };

export function MappingField({ field, value, disabled, onChange }: MappingFieldProps) {
  const rows = toMappingRows(value);
  const labels = field.mappingLabels ?? {
    key: t("mappingField.key"),
    value: t("mappingField.value"),
  };

  const updateRow = (index: number, update: Partial<MappingRow>) => {
    onChange(rows.map((row, position) => (position === index ? { ...row, ...update } : row)));
  };

  return (
    <div className="mapping-field" id={field.name}>
      <div className="mapping-row mapping-header">
        <span>{labels.key}</span>
        <span>{labels.value}</span>
        <span />
      </div>
      {rows.map((row, index) => (
        <div key={index} className="mapping-row">
          <input
            type="text"
            aria-label={`${labels.key} ${String(index + 1)}`}
            value={row.key}
            disabled={disabled}
            onChange={(event) => {
              updateRow(index, { key: event.target.value });
            }}
          />
          <input
            type="text"
            aria-label={`${labels.value} ${String(index + 1)}`}
            value={row.value}
            disabled={disabled}
            onChange={(event) => {
              updateRow(index, { value: event.target.value });
            }}
          />
          <button
            type="button"
            className="icon-button"
            aria-label={t("mappingField.removeRow")}
            disabled={disabled}
            onClick={() => {
              onChange(rows.filter((_, position) => position !== index));
            }}
          >
            <CloseIcon size={14} />
          </button>
        </div>
      ))}
      <button
        type="button"
        className="mapping-add"
        disabled={disabled}
        onClick={() => {
          onChange([...rows, EMPTY_ROW]);
        }}
      >
        {t("mappingField.addRow")}
      </button>
    </div>
  );
}

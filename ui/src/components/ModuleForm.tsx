import {
  fieldInputId,
  isPathKind,
  toTextValue,
  type FieldDescriptor,
  type FormValue,
  type FormValues,
} from "../lib/form-schema";
import { MappingField } from "./MappingField";
import { PathField } from "./PathField";

interface ModuleFormProps {
  moduleId: string;
  fields: FieldDescriptor[];
  values: FormValues;
  disabled: boolean;
  onChange: (name: string, value: FormValue) => void;
}

export function ModuleForm({ moduleId, fields, values, disabled, onChange }: ModuleFormProps) {
  return (
    <form
      className="module-form"
      onSubmit={(event) => {
        event.preventDefault();
      }}
    >
      {fields.map((field) => (
        <div key={field.name} className="form-field">
          <label htmlFor={fieldInputId(moduleId, field.name)}>
            {field.label}
            {field.required && <span className="required"> *</span>}
          </label>
          <FieldInput
            moduleId={moduleId}
            field={field}
            value={values[field.name] ?? field.defaultValue}
            disabled={disabled}
            onChange={(value) => {
              onChange(field.name, value);
            }}
          />
          {field.description && <small>{field.description}</small>}
        </div>
      ))}
    </form>
  );
}

interface FieldInputProps {
  moduleId: string;
  field: FieldDescriptor;
  value: FormValue;
  disabled: boolean;
  onChange: (value: FormValue) => void;
}

function FieldInput({ moduleId, field, value, disabled, onChange }: FieldInputProps) {
  if (isPathKind(field.kind)) {
    return (
      <PathField
        moduleId={moduleId}
        field={field}
        value={value}
        disabled={disabled}
        onChange={onChange}
      />
    );
  }
  if (field.kind === "mapping") {
    return (
      <MappingField
        moduleId={moduleId}
        field={field}
        value={value}
        disabled={disabled}
        onChange={onChange}
      />
    );
  }
  if (field.kind === "bool") {
    return (
      <input
        id={fieldInputId(moduleId, field.name)}
        type="checkbox"
        checked={value === true}
        disabled={disabled}
        onChange={(event) => {
          onChange(event.target.checked);
        }}
      />
    );
  }
  if (field.kind === "enum") {
    return (
      <select
        id={fieldInputId(moduleId, field.name)}
        value={toTextValue(value)}
        disabled={disabled}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      >
        {field.options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    );
  }
  return (
    <input
      id={fieldInputId(moduleId, field.name)}
      type={field.kind === "number" ? "number" : "text"}
      value={toTextValue(value)}
      disabled={disabled}
      onChange={(event) => {
        onChange(event.target.value);
      }}
    />
  );
}

import { t } from "../i18n/shell";
import { z } from "zod";

export const UI_KINDS = [
  "file",
  "files",
  "folder",
  "folders",
  "output_folder",
  "template",
  "text",
  "number",
  "bool",
  "enum",
  "mapping",
] as const;

export type UiKind = (typeof UI_KINDS)[number];
export interface MappingRow {
  key: string;
  value: string;
}

export type FormValue = string | string[] | boolean | MappingRow[];
export type FormValues = Record<string, FormValue>;

const MULTIPLE_PATH_KINDS: ReadonlySet<UiKind> = new Set(["files", "folders"]);
const FOLDER_KINDS: ReadonlySet<UiKind> = new Set(["folder", "folders", "output_folder"]);
const PATH_KINDS: ReadonlySet<UiKind> = new Set([
  "file",
  "files",
  "folder",
  "folders",
  "output_folder",
  "template",
]);

const propertySchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  "x-ui": z.enum(UI_KINDS),
  default: z.unknown().optional(),
  enum: z.array(z.string()).optional(),
  $ref: z.string().optional(),
  "x-ui-key-label": z.string().optional(),
  "x-ui-value-label": z.string().optional(),
});

const mappingRowsSchema = z.array(z.object({ key: z.string(), value: z.string() }));

export const inputsSchemaSchema = z.object({
  properties: z.record(z.string(), propertySchema),
  required: z.array(z.string()).optional(),
  $defs: z.record(z.string(), z.object({ enum: z.array(z.string()).optional() })).optional(),
});

export type InputsSchema = z.infer<typeof inputsSchemaSchema>;
type PropertySchema = z.infer<typeof propertySchema>;

export interface FieldDescriptor {
  name: string;
  label: string;
  description: string | null;
  kind: UiKind;
  required: boolean;
  options: string[];
  defaultValue: FormValue;
  mappingLabels: { key: string; value: string } | null;
}

export function isPathKind(kind: UiKind): boolean {
  return PATH_KINDS.has(kind);
}

export function isMultipleKind(kind: UiKind): boolean {
  return MULTIPLE_PATH_KINDS.has(kind);
}

export function isFolderKind(kind: UiKind): boolean {
  return FOLDER_KINDS.has(kind);
}

export function describeFields(schema: InputsSchema): FieldDescriptor[] {
  const required = new Set(schema.required ?? []);
  return Object.entries(schema.properties).map(([name, property]) => {
    const options = resolveOptions(schema, property);
    return {
      name,
      label: property.title ?? name,
      description: property.description ?? null,
      kind: property["x-ui"],
      required: required.has(name),
      options,
      defaultValue: defaultValueFor(property["x-ui"], property.default, options),
      mappingLabels: mappingLabelsFor(property),
    };
  });
}

const INPUT_ID_SEPARATOR = "-";

/** Every workspace stays mounted, so a label must point at its own module's input, not a namesake. */
export function fieldInputId(namespace: string, fieldName: string): string {
  return `${namespace}${INPUT_ID_SEPARATOR}${fieldName}`;
}

const LABEL_ID_SUFFIX = "-label";

export function fieldLabelId(namespace: string, fieldName: string): string {
  return `${fieldInputId(namespace, fieldName)}${LABEL_ID_SUFFIX}`;
}

/** Path lists and mappings hold several controls: a group named by the label, not a single input. */
export function isGroupKind(kind: UiKind): boolean {
  return kind === "mapping" || isPathKind(kind);
}

export function initialValues(fields: FieldDescriptor[]): FormValues {
  return Object.fromEntries(fields.map((field) => [field.name, field.defaultValue]));
}

/** Labels of the required fields still empty: a run started with them would only fail. */
export function missingRequired(fields: FieldDescriptor[], values: FormValues): string[] {
  return fields
    .filter((field) => field.required && isEmpty(values[field.name]))
    .map((field) => field.label);
}

export function toEngineInputs(fields: FieldDescriptor[], values: FormValues): FormValues {
  const entries = fields
    .map((field): [string, FormValue | undefined] => [field.name, values[field.name]])
    .filter((entry): entry is [string, FormValue] => !isEmpty(entry[1]));
  return Object.fromEntries(entries);
}

export function mergeDroppedPaths(kind: UiKind, current: FormValue, dropped: string[]): FormValue {
  if (!isMultipleKind(kind)) {
    return dropped[0] ?? current;
  }
  return [...new Set([...toPathList(current), ...dropped])];
}

export function toPathList(value: FormValue): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string");
  }
  return typeof value === "string" && value !== "" ? [value] : [];
}

export function toTextValue(value: FormValue): string {
  return typeof value === "string" ? value : "";
}

export function toMappingRows(value: FormValue): MappingRow[] {
  const parsed = mappingRowsSchema.safeParse(value);
  return parsed.success ? parsed.data : [];
}

function mappingLabelsFor(property: PropertySchema): FieldDescriptor["mappingLabels"] {
  if (property["x-ui"] !== "mapping") {
    return null;
  }
  return {
    key: property["x-ui-key-label"] ?? t("mappingField.key"),
    value: property["x-ui-value-label"] ?? t("mappingField.value"),
  };
}

function resolveOptions(schema: InputsSchema, property: PropertySchema): string[] {
  if (property.enum) {
    return property.enum;
  }
  const definitionName = property.$ref?.split("/").at(-1);
  return definitionName ? (schema.$defs?.[definitionName]?.enum ?? []) : [];
}

function defaultValueFor(kind: UiKind, declared: unknown, options: string[]): FormValue {
  const value = toFormValue(kind, declared);
  return kind === "enum" && value === "" ? (options[0] ?? "") : value;
}

export function toFormValue(kind: UiKind, raw: unknown): FormValue {
  if (kind === "bool") {
    return raw === true;
  }
  if (kind === "mapping") {
    const parsed = mappingRowsSchema.safeParse(raw);
    return parsed.success ? parsed.data : [];
  }
  if (isMultipleKind(kind)) {
    return Array.isArray(raw) ? raw.map(String) : [];
  }
  if (typeof raw === "string" || typeof raw === "number") {
    return String(raw);
  }
  return "";
}

function isEmpty(value: FormValue | undefined): boolean {
  return value === undefined || value === "" || (Array.isArray(value) && value.length === 0);
}

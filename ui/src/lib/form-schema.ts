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
] as const;

export type UiKind = (typeof UI_KINDS)[number];
export type FormValue = string | string[] | boolean;
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
});

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
    };
  });
}

export function initialValues(fields: FieldDescriptor[]): FormValues {
  return Object.fromEntries(fields.map((field) => [field.name, field.defaultValue]));
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
  const existing = Array.isArray(current) ? current : [];
  return [...new Set([...existing, ...dropped])];
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

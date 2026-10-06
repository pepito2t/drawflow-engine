import type { RunProposal } from "./assistant-chat";
import type { FieldDescriptor } from "./form-schema";

export interface InputLine {
  label: string;
  value: string;
}

const YES = "oui";
const NO = "non";
const LIST_SEPARATOR = ", ";

/** What the user reads before confirming: only the inputs that carry a value. */
export function describeInputs(
  inputs: Record<string, unknown>,
  fields: FieldDescriptor[],
): InputLine[] {
  return Object.entries(inputs).flatMap(([name, raw]) => {
    const value = displayValue(raw);
    if (value === null) {
      return [];
    }
    const label = fields.find((field) => field.name === name)?.label ?? name;
    return [{ label, value }];
  });
}

export function proposalTitle(proposal: RunProposal): string {
  switch (proposal.kind) {
    case "preset":
      return `${proposal.featureName} — préréglage « ${proposal.label} »`;
    case "synonyms":
      return `Ajouter des en-têtes reconnus (${proposal.featureName})`;
    case "feature":
      return proposal.featureName;
  }
}

/** One line per column: which new header names the assistant wants it to recognize. */
export function describeSynonyms(inputs: Record<string, unknown>): InputLine[] {
  const columns = inputs.columns;
  if (typeof columns !== "object" || columns === null) {
    return [];
  }
  return Object.entries(columns).flatMap(([column, names]) => {
    const value = displayValue(names);
    return value === null ? [] : [{ label: column, value }];
  });
}

function displayValue(raw: unknown): string | null {
  if (typeof raw === "boolean") {
    return raw ? YES : NO;
  }
  if (typeof raw === "number") {
    return String(raw);
  }
  if (typeof raw === "string") {
    return raw.trim() === "" ? null : raw;
  }
  if (Array.isArray(raw)) {
    const items = raw.filter((item): item is string => typeof item === "string" && item !== "");
    return items.length > 0 ? items.join(LIST_SEPARATOR) : null;
  }
  return null;
}

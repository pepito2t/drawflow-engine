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
  return proposal.kind === "preset"
    ? `${proposal.featureName} — préréglage « ${proposal.label} »`
    : proposal.featureName;
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

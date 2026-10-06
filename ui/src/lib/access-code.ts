import { t } from "../i18n/settings";

export type AccessCodeIssue = "mismatch" | "unchanged" | null;

export function checkNewAccessCode(
  current: string,
  next: string,
  confirmation: string,
): AccessCodeIssue {
  if (next !== confirmation) {
    return "mismatch";
  }
  return next === current ? "unchanged" : null;
}

const ISSUE_KEYS = { mismatch: "accessCode.mismatch", unchanged: "accessCode.unchanged" } as const;

export function accessCodeIssueMessage(issue: Exclude<AccessCodeIssue, null>): string {
  return t(ISSUE_KEYS[issue]);
}

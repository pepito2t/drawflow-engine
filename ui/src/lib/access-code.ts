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

export const ACCESS_CODE_ISSUE_MESSAGES: Record<Exclude<AccessCodeIssue, null>, string> = {
  mismatch: "La confirmation ne correspond pas au nouveau code.",
  unchanged: "Le nouveau code doit être différent de l'actuel.",
};

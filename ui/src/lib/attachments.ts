const ATTACHMENTS_HEADING = "Fichiers joints :";
const DEFAULT_QUESTION = "Que peux-tu faire avec ces fichiers ?";
const PATH_SEPARATORS = /[\\/]/;

/** The paths travel inside the message text: visible to the user, readable by the model. */
export function withAttachments(question: string, paths: string[]): string {
  const text = question.trim();
  if (paths.length === 0) {
    return text;
  }
  const list = paths.map((path) => `- ${path}`).join("\n");
  return `${text || DEFAULT_QUESTION}\n\n${ATTACHMENTS_HEADING}\n${list}`;
}

export function addAttachments(current: string[], dropped: string[]): string[] {
  return [...new Set([...current, ...dropped])];
}

export function fileName(path: string): string {
  return path.split(PATH_SEPARATORS).at(-1) ?? path;
}

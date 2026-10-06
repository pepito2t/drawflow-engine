import { z } from "zod";
import { t } from "../i18n/shell";
import { parseEventLine } from "./events";

const engineOutputSchema = z.object({ success: z.boolean(), stdout: z.string() });

export class EngineCommandError extends Error {
  override name = "EngineCommandError";

  constructor(
    message: string,
    readonly hint: string | null,
    readonly file: string | null,
  ) {
    super(message);
  }
}

export function unwrapEngineOutput(raw: unknown): string {
  const output = engineOutputSchema.parse(raw);
  if (output.success) {
    return output.stdout;
  }
  throw toCommandError(output.stdout);
}

function toCommandError(stdout: string): EngineCommandError {
  const lastLine = stdout.trim().split("\n").at(-1) ?? "";
  const event = lastLine ? parseEventLine(lastLine) : null;
  if (event?.type === "error") {
    return new EngineCommandError(event.message, event.hint, event.file);
  }
  return new EngineCommandError(t("engineOutput.failure"), null, null);
}

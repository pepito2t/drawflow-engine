import { z } from "zod";
import { CatalogError } from "./catalog";
import { parseJsonOrNull } from "./json";

const assistantStatusSchema = z.object({
  server_url: z.string(),
  model: z.string(),
  available: z.array(z.string()),
  installed: z.boolean(),
});

export type AssistantStatus = z.infer<typeof assistantStatusSchema>;

export function parseAssistantStatus(rawJson: string): AssistantStatus {
  const parsed = assistantStatusSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new CatalogError("L'état de l'assistant reçu du moteur est invalide.");
  }
  return parsed.data;
}

// Embedding models are listed by the same API but cannot answer a conversation.
const EMBEDDING_MODEL = /embed/i;

export function selectableModels(status: AssistantStatus): string[] {
  const chatModels = status.available.filter((name) => !EMBEDDING_MODEL.test(name));
  return chatModels.includes(status.model) ? chatModels : [status.model, ...chatModels];
}

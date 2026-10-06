import { z } from "zod";
import { parseJsonOrNull } from "./json";

const participantSchema = z.object({ name: z.string(), address: z.string() });

const attachmentSchema = z.object({
  name: z.string(),
  size: z.number().int(),
  content_type: z.string(),
  file: z.string().nullable(),
});

const messageSchema = z.object({
  id: z.string(),
  received_at: z.string(),
  sender: participantSchema,
  recipients: z.array(participantSchema),
  subject: z.string(),
  preview: z.string(),
  body: z.string(),
  attachments: z.array(attachmentSchema),
  web_link: z.string().nullable(),
});

const conversationSchema = z.object({
  id: z.string(),
  subject: z.string(),
  participants: z.array(participantSchema),
  first_received_at: z.string(),
  last_received_at: z.string(),
  message_count: z.number().int(),
  attachment_count: z.number().int(),
  project: z.string().nullable(),
  category: z.string().nullable(),
});

const statusSchema = z.object({
  configured: z.boolean(),
  account: z.string().nullable(),
  last_fetch_at: z.string().nullable(),
  conversations: z.number().int(),
  folder: z.string(),
});

const deviceLoginSchema = z.object({
  device_code: z.string(),
  user_code: z.string(),
  verification_uri: z.string(),
  interval: z.number().int(),
  expires_in: z.number().int(),
});

const fetchResultSchema = z.object({
  fetched: z.number().int(),
  added: z.number().int(),
  conversations: z.number().int(),
  pruned: z.number().int(),
});

const listSchema = z.object({ conversations: z.array(conversationSchema) });
const detailSchema = z.object({
  conversation: conversationSchema,
  messages: z.array(messageSchema),
});

export type MailParticipant = z.infer<typeof participantSchema>;
export type MailMessage = z.infer<typeof messageSchema>;
export type MailConversation = z.infer<typeof conversationSchema>;
export type MailStatus = z.infer<typeof statusSchema>;
export type DeviceLogin = z.infer<typeof deviceLoginSchema>;
export type MailFetchResult = z.infer<typeof fetchResultSchema>;
export type MailDetail = z.infer<typeof detailSchema>;

export class MailParseError extends Error {
  override name = "MailParseError";
}

function parse<T>(schema: z.ZodType<T>, rawJson: string, what: string): T {
  const parsed = schema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new MailParseError(`Réponse du moteur invalide (${what}).`);
  }
  return parsed.data;
}

export const parseMailStatus = (raw: string) => parse(statusSchema, raw, "état des courriels");
export const parseDeviceLogin = (raw: string) => parse(deviceLoginSchema, raw, "connexion");
export const parseFetchResult = (raw: string) => parse(fetchResultSchema, raw, "récupération");
export const parseConversations = (raw: string) =>
  parse(listSchema, raw, "conversations").conversations;
export const parseMailDetail = (raw: string) => parse(detailSchema, raw, "conversation");

export function describeParticipant(person: MailParticipant): string {
  return person.name || person.address || "inconnu";
}

export function describeFetch(result: MailFetchResult): string {
  if (result.added === 0) {
    return "Aucun nouveau message.";
  }
  const messages = result.added > 1 ? "nouveaux messages" : "nouveau message";
  return `${String(result.added)} ${messages}, ${String(result.conversations)} conversations.`;
}

export function describeReceived(instant: string): string {
  const date = new Date(instant);
  return Number.isNaN(date.getTime())
    ? instant
    : date.toLocaleString("fr-CH", { dateStyle: "medium", timeStyle: "short" });
}

export function participantsSummary(conversation: MailConversation, max = 3): string {
  const names = conversation.participants.map(describeParticipant);
  const shown = names.slice(0, max).join(", ");
  return names.length > max ? `${shown} +${String(names.length - max)}` : shown;
}

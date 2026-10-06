import { z } from "zod";
import type { AssistantEvent } from "./assistant-events";
import { parseJsonOrNull } from "./json";
import type { ReadableError } from "./error-message";

export type ToolStatus = "running" | "succeeded" | "failed";
export type AnswerStatus = "streaming" | "done" | "failed" | "cancelled";

export interface ToolActivity {
  id: string;
  name: string;
  status: ToolStatus;
}

export type ProposalStatus = "pending" | "launching" | "launched" | "dismissed" | "failed";

export interface RunProposal {
  id: string;
  kind: "preset" | "feature" | "synonyms";
  feature: string;
  featureName: string;
  label: string;
  presetId: string | null;
  inputs: Record<string, unknown>;
  status: ProposalStatus;
  error: string | null;
}

export interface UserEntry {
  role: "user";
  id: number;
  text: string;
}

export interface AssistantEntry {
  role: "assistant";
  id: number;
  text: string;
  tools: ToolActivity[];
  proposals: RunProposal[];
  status: AnswerStatus;
  error: ReadableError | null;
}

export type ChatEntry = UserEntry | AssistantEntry;

export interface ChatState {
  entries: ChatEntry[];
  nextId: number;
}

/** `answerId` ties late messages of a stopped answer to that answer, never to the next one. */
export type ChatAction =
  | { type: "sent"; text: string }
  | { type: "event"; answerId: number; event: AssistantEvent }
  | { type: "exited"; answerId: number; code: number | null }
  | { type: "failed"; answerId: number; error: ReadableError }
  | { type: "cancelled" }
  | { type: "cleared" }
  | { type: "restored"; messages: ConversationMessage[] }
  | { type: "proposal"; proposalId: string; status: ProposalStatus; error?: string };

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

const savedHistorySchema = z.object({
  messages: z.array(z.object({ role: z.enum(["user", "assistant"]), content: z.string().min(1) })),
});

export const INITIAL_CHAT: ChatState = { entries: [], nextId: 1 };

const SUCCESS_EXIT_CODE = 0;
const UNEXPECTED_EXIT: ReadableError = {
  message: "L'assistant s'est arrêté sans terminer sa réponse.",
  hint: "Réessayez ; si le problème persiste, vérifiez Paramètres → Assistant.",
  file: null,
};
const TOOL_LABELS: Record<string, string> = {
  list_features: "Consulte les fonctionnalités",
  list_presets: "Consulte les préréglages",
  list_templates: "Consulte les modèles",
};

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "sent":
      return startAnswer(state, action.text);
    case "event":
      return updateAnswer(state, action.answerId, (answer) => applyEvent(answer, action.event));
    case "exited":
      return updateAnswer(state, action.answerId, (answer) =>
        action.code === SUCCESS_EXIT_CODE
          ? { ...answer, status: "done" }
          : { ...answer, status: "failed", error: answer.error ?? UNEXPECTED_EXIT },
      );
    case "failed":
      return updateAnswer(state, action.answerId, (answer) => ({
        ...answer,
        status: "failed",
        error: action.error,
      }));
    case "cancelled": {
      const answer = streamingAnswer(state);
      return answer ? updateAnswer(state, answer.id, settleTools("cancelled")) : state;
    }
    case "cleared":
      return { entries: [], nextId: state.nextId };
    case "proposal":
      return updateProposal(state, action.proposalId, action.status, action.error ?? null);
    case "restored":
      return state.entries.length === 0 ? restore(action.messages, state.nextId) : state;
  }
}

/** The texts worth keeping between launches; run proposals are never restored. */
export function savedHistory(state: ChatState): ConversationMessage[] {
  return state.entries.flatMap((entry): ConversationMessage[] => {
    const content = entry.text.trim();
    return content ? [{ role: entry.role, content }] : [];
  });
}

export function parseSavedHistory(rawJson: string): ConversationMessage[] {
  const parsed = savedHistorySchema.safeParse(parseJsonOrNull(rawJson));
  return parsed.success ? parsed.data.messages : [];
}

function restore(messages: ConversationMessage[], firstId: number): ChatState {
  const entries = messages.map((message, index): ChatEntry => {
    const id = firstId + index;
    return message.role === "user"
      ? { role: "user", id, text: message.content }
      : {
          role: "assistant",
          id,
          text: message.content,
          tools: [],
          proposals: [],
          status: "done",
          error: null,
        };
  });
  return { entries, nextId: firstId + messages.length };
}

export function streamingAnswer(state: ChatState): AssistantEntry | null {
  const last = state.entries.at(-1);
  return last?.role === "assistant" && last.status === "streaming" ? last : null;
}

export function conversationWith(state: ChatState, question: string): ConversationMessage[] {
  return [...savedHistory(state), { role: "user", content: question }];
}

export function toolLabel(name: string): string {
  return TOOL_LABELS[name] ?? `Outil ${name}`;
}

function startAnswer(state: ChatState, text: string): ChatState {
  const question: UserEntry = { role: "user", id: state.nextId, text };
  const answer: AssistantEntry = {
    role: "assistant",
    id: state.nextId + 1,
    text: "",
    tools: [],
    proposals: [],
    status: "streaming",
    error: null,
  };
  return { entries: [...state.entries, question, answer], nextId: state.nextId + 2 };
}

function updateAnswer(
  state: ChatState,
  answerId: number,
  update: (answer: AssistantEntry) => AssistantEntry,
): ChatState {
  const answer = streamingAnswer(state);
  if (answer?.id !== answerId) {
    return state;
  }
  return { ...state, entries: [...state.entries.slice(0, -1), update(answer)] };
}

function applyEvent(answer: AssistantEntry, event: AssistantEvent): AssistantEntry {
  switch (event.type) {
    case "delta":
      return { ...answer, text: answer.text + event.text };
    case "tool_call":
      return {
        ...answer,
        tools: [...answer.tools, { id: event.id, name: event.name, status: "running" }],
      };
    case "tool_result":
      return {
        ...answer,
        tools: answer.tools.map((tool) =>
          tool.id === event.id ? { ...tool, status: event.ok ? "succeeded" : "failed" } : tool,
        ),
      };
    case "proposal":
      return {
        ...answer,
        proposals: [
          ...answer.proposals,
          {
            id: event.id,
            kind: event.kind,
            feature: event.feature,
            featureName: event.feature_name,
            label: event.label,
            presetId: event.preset_id,
            inputs: event.inputs,
            status: "pending",
            error: null,
          },
        ],
      };
    case "done":
      return settleTools("done")(answer);
    case "error":
      return {
        ...settleTools("failed")(answer),
        error: { message: event.message, hint: event.hint, file: event.file },
      };
  }
}

/** Proposals stay actionable after the answer ends, so they are found in any entry. */
function updateProposal(
  state: ChatState,
  proposalId: string,
  status: ProposalStatus,
  error: string | null,
): ChatState {
  return {
    ...state,
    entries: state.entries.map((entry) =>
      entry.role === "assistant" && entry.proposals.some((p) => p.id === proposalId)
        ? {
            ...entry,
            proposals: entry.proposals.map((p) =>
              p.id === proposalId ? { ...p, status, error } : p,
            ),
          }
        : entry,
    ),
  };
}

function settleTools(status: AnswerStatus): (answer: AssistantEntry) => AssistantEntry {
  return (answer) => ({
    ...answer,
    status,
    tools: answer.tools.map((tool) =>
      tool.status === "running" ? { ...tool, status: "failed" } : tool,
    ),
  });
}

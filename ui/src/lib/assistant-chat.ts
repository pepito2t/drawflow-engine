import type { AssistantEvent } from "./assistant-events";
import type { ReadableError } from "./error-message";

export type ToolStatus = "running" | "succeeded" | "failed";
export type AnswerStatus = "streaming" | "done" | "failed" | "cancelled";

export interface ToolActivity {
  id: string;
  name: string;
  status: ToolStatus;
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
  | { type: "cleared" };

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

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
  }
}

export function streamingAnswer(state: ChatState): AssistantEntry | null {
  const last = state.entries.at(-1);
  return last?.role === "assistant" && last.status === "streaming" ? last : null;
}

export function conversationWith(state: ChatState, question: string): ConversationMessage[] {
  const history = state.entries.flatMap((entry): ConversationMessage[] => {
    const content = entry.text.trim();
    return content ? [{ role: entry.role, content }] : [];
  });
  return [...history, { role: "user", content: question }];
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
    case "done":
      return settleTools("done")(answer);
    case "error":
      return {
        ...settleTools("failed")(answer),
        error: { message: event.message, hint: event.hint, file: event.file },
      };
  }
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

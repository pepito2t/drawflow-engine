import { useCallback, useReducer } from "react";
import { parseAssistantLine } from "../lib/assistant-events";
import {
  chatReducer,
  conversationWith,
  INITIAL_CHAT,
  streamingAnswer,
  type ChatState,
  type ProposalStatus,
} from "../lib/assistant-chat";
import { toReadableError } from "../lib/error-message";
import { cancelAssistant, startAssistantChat } from "../lib/tauri/assistant";

interface AssistantChat {
  state: ChatState;
  isAnswering: boolean;
  ask: (question: string) => void;
  stop: () => void;
  clear: () => void;
  markProposal: (proposalId: string, status: ProposalStatus, error?: string) => void;
}

export function useAssistantChat(): AssistantChat {
  const [state, dispatch] = useReducer(chatReducer, INITIAL_CHAT);
  const isAnswering = streamingAnswer(state) !== null;

  const ask = useCallback(
    (question: string) => {
      const text = question.trim();
      if (!text || isAnswering) {
        return;
      }
      const answerId = state.nextId + 1;
      const conversation = conversationWith(state, text);
      dispatch({ type: "sent", text });
      startAssistantChat(conversation, (message) => {
        if (message.kind === "stdout") {
          dispatch({ type: "event", answerId, event: parseAssistantLine(message.line) });
        } else if (message.kind === "exit") {
          dispatch({ type: "exited", answerId, code: message.code });
        } else {
          console.warn("Assistant :", message.line);
        }
      }).catch((error: unknown) => {
        dispatch({ type: "failed", answerId, error: toReadableError(error) });
      });
    },
    [state, isAnswering],
  );

  const stop = useCallback(() => {
    dispatch({ type: "cancelled" });
    cancelAssistant().catch((error: unknown) => {
      console.error("Arrêt de l'assistant impossible :", error);
    });
  }, []);

  const clear = useCallback(() => {
    if (isAnswering) {
      stop();
    }
    dispatch({ type: "cleared" });
  }, [isAnswering, stop]);

  const markProposal = useCallback((proposalId: string, status: ProposalStatus, error?: string) => {
    dispatch(
      error === undefined
        ? { type: "proposal", proposalId, status }
        : { type: "proposal", proposalId, status, error },
    );
  }, []);

  return { state, isAnswering, ask, stop, clear, markProposal };
}

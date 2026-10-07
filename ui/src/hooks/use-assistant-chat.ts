import { useCallback, useEffect, useReducer, useRef } from "react";
import { parseAssistantLine } from "../lib/assistant-events";
import {
  chatReducer,
  conversationWith,
  INITIAL_CHAT,
  parseSavedHistory,
  savedHistory,
  streamingAnswer,
  type ChatAction,
  type ChatState,
  type ProposalStatus,
} from "../lib/assistant-chat";
import { toReadableError } from "../lib/error-message";
import {
  cancelAssistant,
  getAssistantHistory,
  saveAssistantHistory,
  startAssistantChat,
} from "../lib/tauri/assistant";

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
  useConversationStorage(state, isAnswering, dispatch);

  const ask = useCallback(
    (question: string) => {
      const text = question.trim();
      if (!text || isAnswering) {
        return;
      }
      const answerId = state.nextId + 1;
      const conversation = conversationWith(state, text);
      dispatch({ type: "sent", text });
      const fail = (error: unknown) => {
        dispatch({ type: "failed", answerId, error: toReadableError(error) });
      };
      startAssistantChat(
        conversation,
        (message) => {
          if (message.kind === "stdout") {
            dispatch({ type: "event", answerId, event: parseAssistantLine(message.line) });
          } else if (message.kind === "exit") {
            dispatch({ type: "exited", answerId, code: message.code });
          } else {
            console.warn("Assistant :", message.line);
          }
        },
        fail,
      ).catch(fail);
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
    saveAssistantHistory([]).catch(reportStorageError);
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

/** Restores the last conversation once, then saves it each time an answer ends. */
function useConversationStorage(
  state: ChatState,
  isAnswering: boolean,
  dispatch: (action: ChatAction) => void,
): void {
  const wasAnswering = useRef(false);

  useEffect(() => {
    let isActive = true;
    getAssistantHistory()
      .then((raw) => {
        if (isActive) {
          dispatch({ type: "restored", messages: parseSavedHistory(raw) });
        }
      })
      .catch(reportStorageError);
    return () => {
      isActive = false;
    };
  }, [dispatch]);

  useEffect(() => {
    if (wasAnswering.current && !isAnswering) {
      saveAssistantHistory(savedHistory(state)).catch(reportStorageError);
    }
    wasAnswering.current = isAnswering;
  }, [isAnswering, state]);
}

function reportStorageError(error: unknown): void {
  console.error("Conversation de l'assistant non enregistrée :", error);
}

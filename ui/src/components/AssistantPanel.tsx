import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useAssistantChat } from "../hooks/use-assistant-chat";
import type { CatalogModule } from "../lib/catalog";
import { AssistantConnection } from "./AssistantConnection";
import { AssistantMessage } from "./AssistantMessage";
import { CloseIcon, PlusIcon, SendIcon, StopIcon } from "./icons";

const SUGGESTIONS = [
  "Quelles fonctionnalités propose Drawflow ?",
  "Quels préréglages sont enregistrés ?",
  "Lance la liste de pièces sur un dossier de plans",
];

interface AssistantPanelProps {
  modules: CatalogModule[];
  isOpen: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
}

export function AssistantPanel({ modules, isOpen, onClose, onOpenSettings }: AssistantPanelProps) {
  const { state, isAnswering, ask, stop, clear, markProposal } = useAssistantChat();
  const [draft, setDraft] = useState("");
  const messagesRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const list = messagesRef.current;
    list?.scrollTo({ top: list.scrollHeight });
  }, [state.entries]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  const submit = (question: string) => {
    if (!question.trim() || isAnswering) {
      return;
    }
    ask(question);
    setDraft("");
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit(draft);
    }
  };

  return (
    <aside className="assistant-panel" aria-label="Assistant" hidden={!isOpen}>
      <header className="assistant-header">
        <strong>Assistant</strong>
        <div className="assistant-actions">
          <button
            type="button"
            className="icon-button"
            aria-label="Nouvelle conversation"
            title="Nouvelle conversation"
            disabled={state.entries.length === 0}
            onClick={clear}
          >
            <PlusIcon />
          </button>
          <button
            type="button"
            className="icon-button"
            aria-label="Fermer l'assistant"
            title="Fermer"
            onClick={onClose}
          >
            <CloseIcon />
          </button>
        </div>
      </header>
      <AssistantConnection onOpenSettings={onOpenSettings} />
      <div className="assistant-messages" ref={messagesRef} aria-live="polite">
        {state.entries.length === 0 && (
          <div className="assistant-empty">
            <p className="muted">
              Posez une question sur Drawflow. L'assistant tourne sur un modèle local : rien ne
              quitte ce poste.
            </p>
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="assistant-suggestion"
                onClick={() => {
                  submit(suggestion);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
        {state.entries.map((entry) => (
          <AssistantMessage
            key={entry.id}
            entry={entry}
            modules={modules}
            onProposal={markProposal}
          />
        ))}
      </div>
      <form
        className="assistant-composer"
        onSubmit={(event) => {
          event.preventDefault();
          submit(draft);
        }}
      >
        <textarea
          ref={inputRef}
          value={draft}
          rows={3}
          placeholder="Votre question… (Maj+Entrée pour un retour à la ligne)"
          aria-label="Question pour l'assistant"
          onChange={(event) => {
            setDraft(event.target.value);
          }}
          onKeyDown={onKeyDown}
        />
        {isAnswering ? (
          <button
            type="button"
            className="icon-button"
            aria-label="Arrêter"
            title="Arrêter"
            onClick={stop}
          >
            <StopIcon />
          </button>
        ) : (
          <button
            type="submit"
            className="icon-button primary-icon"
            aria-label="Envoyer"
            title="Envoyer"
            disabled={!draft.trim()}
          >
            <SendIcon />
          </button>
        )}
      </form>
    </aside>
  );
}

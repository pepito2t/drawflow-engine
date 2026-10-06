import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useAssistantChat } from "../hooks/use-assistant-chat";
import { dropFieldProps, useFileDrop } from "../hooks/use-file-drop";
import { t } from "../i18n/panels";
import { addAttachments, fileName, withAttachments } from "../lib/attachments";
import type { CatalogModule } from "../lib/catalog";
import { AssistantConnection } from "./AssistantConnection";
import { AssistantMessage } from "./AssistantMessage";
import { CloseIcon, PlusIcon, SendIcon, StopIcon } from "./icons";

const ASSISTANT_DROP_NAMESPACE = "assistant";
const ATTACHMENTS_FIELD = "attachments";

const SUGGESTIONS = [
  "assistant.suggestion.features",
  "assistant.suggestion.presets",
  "assistant.suggestion.parts",
] as const;

interface AssistantPanelProps {
  modules: CatalogModule[];
  isOpen: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
}

export function AssistantPanel({ modules, isOpen, onClose, onOpenSettings }: AssistantPanelProps) {
  const { state, isAnswering, ask, stop, clear, markProposal } = useAssistantChat();
  const [draft, setDraft] = useState("");
  const [attachments, setAttachments] = useState<string[]>([]);
  const onDrop = useCallback((_field: string, paths: string[]) => {
    setAttachments((current) => addAttachments(current, paths));
  }, []);
  useFileDrop(ASSISTANT_DROP_NAMESPACE, onDrop);
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
    if ((!question.trim() && attachments.length === 0) || isAnswering) {
      return;
    }
    ask(withAttachments(question, attachments));
    setDraft("");
    setAttachments([]);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit(draft);
    }
  };

  return (
    <aside className="assistant-panel" aria-label={t("assistant.title")} hidden={!isOpen}>
      <header className="assistant-header">
        <strong>{t("assistant.title")}</strong>
        <div className="assistant-actions">
          <button
            type="button"
            className="icon-button"
            aria-label={t("assistant.new_conversation")}
            title={t("assistant.new_conversation")}
            disabled={state.entries.length === 0}
            onClick={clear}
          >
            <PlusIcon />
          </button>
          <button
            type="button"
            className="icon-button"
            aria-label={t("assistant.close")}
            title={t("assistant.close_short")}
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
            <p className="muted">{t("assistant.intro")}</p>
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="assistant-suggestion"
                onClick={() => {
                  submit(t(suggestion));
                }}
              >
                {t(suggestion)}
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
        {...dropFieldProps(ASSISTANT_DROP_NAMESPACE, ATTACHMENTS_FIELD)}
        onSubmit={(event) => {
          event.preventDefault();
          submit(draft);
        }}
      >
        {attachments.length > 0 && (
          <ul className="assistant-attachments" aria-label={t("assistant.attachments")}>
            {attachments.map((path) => (
              <li key={path} title={path}>
                <span>{fileName(path)}</span>
                <button
                  type="button"
                  className="icon-button"
                  aria-label={t("assistant.remove_attachment", { name: fileName(path) })}
                  onClick={() => {
                    setAttachments((current) => current.filter((item) => item !== path));
                  }}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
        <textarea
          ref={inputRef}
          value={draft}
          rows={3}
          placeholder={t("assistant.placeholder")}
          aria-label={t("assistant.question")}
          onChange={(event) => {
            setDraft(event.target.value);
          }}
          onKeyDown={onKeyDown}
        />
        {isAnswering ? (
          <button
            type="button"
            className="icon-button"
            aria-label={t("assistant.stop")}
            title={t("assistant.stop")}
            onClick={stop}
          >
            <StopIcon />
          </button>
        ) : (
          <button
            type="submit"
            className="icon-button primary-icon"
            aria-label={t("assistant.send")}
            title={t("assistant.send")}
            disabled={!draft.trim() && attachments.length === 0}
          >
            <SendIcon />
          </button>
        )}
      </form>
    </aside>
  );
}

import { toolLabel, type ChatEntry, type ToolActivity } from "../lib/assistant-chat";
import { ErrorPanel } from "./ErrorPanel";
import { CheckIcon, CloseIcon } from "./icons";
import { MarkdownText } from "./MarkdownText";
import { Spinner } from "./Spinner";

const TOOL_ICON_SIZE = 14;

export function AssistantMessage({ entry }: { entry: ChatEntry }) {
  if (entry.role === "user") {
    return <div className="chat-message user">{entry.text}</div>;
  }
  const isThinking = entry.status === "streaming" && entry.text.trim() === "";
  return (
    <div className="chat-message assistant">
      {entry.tools.map((tool) => (
        <ToolLine key={tool.id} tool={tool} />
      ))}
      {entry.text.trim() && <MarkdownText source={entry.text} />}
      {isThinking && <Spinner label="L'assistant réfléchit" />}
      {entry.status === "cancelled" && <p className="muted">Réponse interrompue.</p>}
      {entry.error && (
        <ErrorPanel
          title="L'assistant n'a pas pu répondre"
          message={entry.error.message}
          hint={entry.error.hint}
        />
      )}
    </div>
  );
}

function ToolLine({ tool }: { tool: ToolActivity }) {
  return (
    <div className={`chat-tool ${tool.status}`}>
      {tool.status === "running" && <Spinner label="Outil en cours" />}
      {tool.status === "succeeded" && <CheckIcon size={TOOL_ICON_SIZE} />}
      {tool.status === "failed" && <CloseIcon size={TOOL_ICON_SIZE} />}
      <span>{toolLabel(tool.name)}</span>
    </div>
  );
}

import { Suspense, use, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { toReadableError, type ReadableError } from "../lib/error-message";
import {
  describeFetch,
  describeParticipant,
  describeReceived,
  participantsSummary,
  type DeviceLogin,
  type MailConversation,
  type MailDetail,
  type MailStatus,
} from "../lib/mail";
import { pickPaths } from "../lib/tauri/dialog";
import {
  disconnectMail,
  exportConversation,
  fetchMail,
  finishMailLogin,
  getMailStatus,
  listConversations,
  readConversation,
  removeConversation,
  startMailLogin,
} from "../lib/tauri/mail";
import { openOutput } from "../lib/tauri/window";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader, Spinner } from "./Spinner";

interface MailData {
  status: MailStatus;
  conversations: MailConversation[];
}

function loadMail(): Promise<MailData> {
  return getMailStatus().then(async (status) => ({
    status,
    conversations: status.conversations > 0 ? await listConversations() : [],
  }));
}

export function MailPanel({ onOpenSettings }: { onOpenSettings: () => void }) {
  const { id, promise, retry } = useRetryablePromise(loadMail);
  return (
    <section className="module-workspace">
      <header>
        <h1>Courriels</h1>
        <p>
          Vos conversations Exchange, conservées sur ce poste : lire, exporter vers un dossier de
          chantier, retirer. La boîte mail n'est jamais modifiée.
        </p>
      </header>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <ErrorPanel
              title="Courriels indisponibles"
              message={message}
              hint={hint}
              onRetry={retry}
            />
          );
        }}
      >
        <Suspense fallback={<Loader label="Chargement des courriels…" />}>
          <MailContent dataPromise={promise} onChanged={retry} onOpenSettings={onOpenSettings} />
        </Suspense>
      </ErrorBoundary>
    </section>
  );
}

interface MailContentProps {
  dataPromise: Promise<MailData>;
  onChanged: () => void;
  onOpenSettings: () => void;
}

function MailContent({ dataPromise, onChanged, onOpenSettings }: MailContentProps) {
  const { status, conversations } = use(dataPromise);
  const { publish } = useNotificationCenter();
  const [login, setLogin] = useState<DeviceLogin | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<ReadableError | null>(null);
  const [selected, setSelected] = useState<MailDetail | null>(null);

  const fail = (reason: unknown) => {
    setError(toReadableError(reason));
    setIsBusy(false);
  };
  const run = (work: () => Promise<string | null>) => {
    setIsBusy(true);
    setError(null);
    setNotice(null);
    work()
      .then((message) => {
        setNotice(message);
        setIsBusy(false);
        onChanged();
      })
      .catch(fail);
  };

  const connect = () => {
    run(async () => {
      const started = await startMailLogin();
      setLogin(started);
      await finishMailLogin(started);
      setLogin(null);
      return "Boîte mail connectée.";
    });
  };
  const fetch = () => {
    run(async () => {
      const result = await fetchMail();
      publish({ type: "mailFetched", added: result.added });
      return describeFetch(result);
    });
  };
  const open = (conversation: MailConversation) => {
    setError(null);
    readConversation(conversation.id).then(setSelected).catch(fail);
  };
  const exportSelected = (detail: MailDetail) => {
    pickPaths({ directory: true, multiple: false, title: "Dossier de destination" })
      .then(([target]) => {
        if (target) {
          run(async () => {
            await exportConversation(detail.conversation.id, target);
            return `Conversation exportée dans ${target}.`;
          });
        }
      })
      .catch(fail);
  };
  const removeSelected = (detail: MailDetail) => {
    run(async () => {
      await removeConversation(detail.conversation.id);
      setSelected(null);
      return "Conversation retirée de Drawflow.";
    });
  };

  if (!status.configured) {
    return (
      <div className="mail-setup">
        <p>Renseignez d'abord l'identifiant d'application Entra ID dans Paramètres → Courriel.</p>
        <button type="button" className="primary" onClick={onOpenSettings}>
          Ouvrir les paramètres
        </button>
      </div>
    );
  }

  return (
    <div className="mail-layout">
      <div className="mail-toolbar run-controls">
        {status.account ? (
          <>
            <span className="muted">{status.account}</span>
            <button type="button" className="primary" disabled={isBusy} onClick={fetch}>
              Récupérer les nouveaux messages
            </button>
            <button
              type="button"
              disabled={isBusy}
              onClick={() => {
                run(async () => {
                  await disconnectMail();
                  return "Boîte mail déconnectée.";
                });
              }}
            >
              Déconnecter
            </button>
          </>
        ) : (
          <button type="button" className="primary" disabled={isBusy} onClick={connect}>
            Connecter la boîte mail
          </button>
        )}
        {isBusy && <Spinner label="Courriels en cours" />}
        {notice && <span className="run-status succeeded">{notice}</span>}
      </div>
      {login && (
        <div className="mail-login">
          <p>
            Ouvrez <strong>{login.verification_uri}</strong> et saisissez le code{" "}
            <code className="mail-code">{login.user_code}</code>, puis connectez-vous avec le compte
            de la boîte mail. Drawflow attend la fin de la connexion.
          </p>
        </div>
      )}
      {error && <ErrorPanel title="Action impossible" message={error.message} hint={error.hint} />}
      <div className="mail-columns">
        <ConversationList conversations={conversations} selected={selected} onOpen={open} />
        {selected && (
          <ConversationView
            detail={selected}
            disabled={isBusy}
            onExport={exportSelected}
            onRemove={removeSelected}
          />
        )}
      </div>
    </div>
  );
}

interface ConversationListProps {
  conversations: MailConversation[];
  selected: MailDetail | null;
  onOpen: (conversation: MailConversation) => void;
}

function ConversationList({ conversations, selected, onOpen }: ConversationListProps) {
  if (conversations.length === 0) {
    return <p className="muted">Aucune conversation pour l'instant : récupérez les messages.</p>;
  }
  return (
    <ul className="mail-list" aria-label="Conversations">
      {conversations.map((conversation) => (
        <li key={conversation.id}>
          <button
            type="button"
            className={
              selected?.conversation.id === conversation.id ? "mail-item selected" : "mail-item"
            }
            onClick={() => {
              onOpen(conversation);
            }}
          >
            <strong>{conversation.subject}</strong>
            <span className="muted">{participantsSummary(conversation)}</span>
            <span className="muted">
              {describeReceived(conversation.last_received_at)} ·{" "}
              {String(conversation.message_count)} message
              {conversation.message_count > 1 ? "s" : ""}
              {conversation.attachment_count > 0 &&
                ` · ${String(conversation.attachment_count)} pièce${conversation.attachment_count > 1 ? "s" : ""} jointe${conversation.attachment_count > 1 ? "s" : ""}`}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

interface ConversationViewProps {
  detail: MailDetail;
  disabled: boolean;
  onExport: (detail: MailDetail) => void;
  onRemove: (detail: MailDetail) => void;
}

function ConversationView({ detail, disabled, onExport, onRemove }: ConversationViewProps) {
  const [confirmRemove, setConfirmRemove] = useState(false);
  return (
    <article className="mail-conversation">
      <header className="mail-conversation-header">
        <h2>{detail.conversation.subject}</h2>
        <div className="run-controls">
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              onExport(detail);
            }}
          >
            Exporter vers un dossier…
          </button>
          {confirmRemove ? (
            <>
              <button
                type="button"
                className="primary"
                disabled={disabled}
                onClick={() => {
                  setConfirmRemove(false);
                  onRemove(detail);
                }}
              >
                Confirmer le retrait
              </button>
              <button
                type="button"
                onClick={() => {
                  setConfirmRemove(false);
                }}
              >
                Annuler
              </button>
            </>
          ) : (
            <button
              type="button"
              disabled={disabled}
              onClick={() => {
                setConfirmRemove(true);
              }}
            >
              Retirer de Drawflow
            </button>
          )}
        </div>
      </header>
      {detail.messages.map((message) => (
        <section key={message.id} className="mail-message">
          <div className="mail-message-meta">
            <strong>{describeParticipant(message.sender)}</strong>
            <span className="muted">{describeReceived(message.received_at)}</span>
          </div>
          <span className="muted">
            À : {message.recipients.map(describeParticipant).join(", ") || "—"}
          </span>
          <pre className="mail-body">{message.body || message.preview}</pre>
          {message.attachments.length > 0 && (
            <ul className="mail-attachments">
              {message.attachments.map((attachment) => (
                <li key={attachment.name}>
                  {attachment.file ? (
                    <button
                      type="button"
                      className="link-button"
                      onClick={() => {
                        openOutput(attachment.file ?? "").catch(() => undefined);
                      }}
                    >
                      {attachment.name}
                    </button>
                  ) : (
                    <span className="muted">{attachment.name} (non téléchargée)</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </article>
  );
}

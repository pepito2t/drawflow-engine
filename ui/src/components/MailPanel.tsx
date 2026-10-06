import { Suspense, use, useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { plural } from "../i18n";
import { t } from "../i18n/panels";
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
        <h1>{t("mail.title")}</h1>
        <p>{t("mail.subtitle")}</p>
      </header>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <ErrorPanel
              title={t("mail.unavailable")}
              message={message}
              hint={hint}
              onRetry={retry}
            />
          );
        }}
      >
        <Suspense fallback={<Loader label={t("mail.loading")} />}>
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
      return t("mail.connected");
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
    pickPaths({ directory: true, multiple: false, title: t("mail.pick_folder") })
      .then(([target]) => {
        if (target) {
          run(async () => {
            await exportConversation(detail.conversation.id, target);
            return t("mail.exported", { target });
          });
        }
      })
      .catch(fail);
  };
  const removeSelected = (detail: MailDetail) => {
    run(async () => {
      await removeConversation(detail.conversation.id);
      setSelected(null);
      return t("mail.removed");
    });
  };

  if (!status.configured) {
    return (
      <div className="mail-setup">
        <p>{t("mail.setup_hint")}</p>
        <button type="button" className="primary" onClick={onOpenSettings}>
          {t("mail.open_settings")}
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
              {t("mail.fetch")}
            </button>
            <button
              type="button"
              disabled={isBusy}
              onClick={() => {
                run(async () => {
                  await disconnectMail();
                  return t("mail.disconnected");
                });
              }}
            >
              {t("mail.disconnect")}
            </button>
          </>
        ) : (
          <button type="button" className="primary" disabled={isBusy} onClick={connect}>
            {t("mail.connect")}
          </button>
        )}
        {isBusy && <Spinner label={t("mail.busy")} />}
        {notice && <span className="run-status succeeded">{notice}</span>}
      </div>
      {login && (
        <div className="mail-login">
          <p>
            {t("mail.login.before_uri")} <strong>{login.verification_uri}</strong>{" "}
            {t("mail.login.before_code")} <code className="mail-code">{login.user_code}</code>
            {t("mail.login.after_code")}
          </p>
        </div>
      )}
      {error && (
        <ErrorPanel title={t("common.action_failed")} message={error.message} hint={error.hint} />
      )}
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
    return <p className="muted">{t("mail.empty")}</p>;
  }
  return (
    <ul className="mail-list" aria-label={t("mail.conversations")}>
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
              {plural(conversation.message_count, t("mail.messages.one"), t("mail.messages.other"))}
              {conversation.attachment_count > 0 &&
                ` · ${plural(conversation.attachment_count, t("mail.attachments.one"), t("mail.attachments.other"))}`}
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
            {t("mail.export")}
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
                {t("mail.confirm_remove")}
              </button>
              <button
                type="button"
                onClick={() => {
                  setConfirmRemove(false);
                }}
              >
                {t("common.cancel")}
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
              {t("mail.remove")}
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
            {t("mail.to", {
              recipients: message.recipients.map(describeParticipant).join(", ") || "—",
            })}
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
                    <span className="muted">
                      {t("mail.not_downloaded", { name: attachment.name })}
                    </span>
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

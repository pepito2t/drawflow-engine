import { Suspense, use, useState } from "react";
import { useCommands } from "../hooks/command-registry";
import { useHistory } from "../hooks/history-context";
import { plural } from "../i18n";
import { t } from "../i18n/panels";
import { COMMANDS } from "../lib/commands";
import { toReadableError } from "../lib/error-message";
import { describeDuration, describeStart, lastOutput, type HistoryEntry } from "../lib/history";
import { fileName } from "../lib/paths";
import { clearHistory, removeHistoryEntry } from "../lib/tauri/history";
import { openOutput } from "../lib/tauri/window";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { CloseIcon } from "./icons";
import { Loader } from "./Spinner";

const STATUS_LABELS = {
  succeeded: "history.status.succeeded",
  failed: "history.status.failed",
} as const;

export function HistoryPanel() {
  const { id, promise, reload: retry } = useHistory();

  return (
    <section className="module-workspace">
      <header>
        <h1>{t("history.title")}</h1>
        <p>{t("history.subtitle")}</p>
      </header>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <ErrorPanel
              title={t("history.unavailable")}
              message={message}
              hint={hint}
              onRetry={retry}
            />
          );
        }}
      >
        <Suspense fallback={<Loader label={t("history.loading")} />}>
          <HistoryList entriesPromise={promise} onChanged={retry} />
        </Suspense>
      </ErrorBoundary>
    </section>
  );
}

interface HistoryListProps {
  entriesPromise: Promise<HistoryEntry[]>;
  onChanged: () => void;
}

function HistoryList({ entriesPromise, onChanged }: HistoryListProps) {
  const entries = use(entriesPromise);
  const { execute } = useCommands();
  const [actionError, setActionError] = useState<string | null>(null);
  const [confirmClear, setConfirmClear] = useState(false);

  const fail = (error: unknown) => {
    setActionError(toReadableError(error).message);
  };
  const rerun = (entry: HistoryEntry) => {
    execute(COMMANDS.runFeature, { moduleId: entry.module, inputs: entry.inputs })
      .then((result) => {
        if (!result.ok) setActionError(result.error);
      })
      .catch(fail);
  };
  const open = (path: string) => {
    openOutput(path).catch(fail);
  };
  const remove = (entry: HistoryEntry) => {
    removeHistoryEntry(entry.id).then(onChanged).catch(fail);
  };
  const clear = () => {
    setConfirmClear(false);
    clearHistory().then(onChanged).catch(fail);
  };

  if (entries.length === 0) {
    return <p className="muted">{t("history.empty")}</p>;
  }
  return (
    <>
      <ul className="history-list">
        {entries.map((entry) => (
          <HistoryRow
            key={entry.id}
            entry={entry}
            onOpen={open}
            onRerun={rerun}
            onRemove={remove}
          />
        ))}
      </ul>
      {actionError && <ErrorPanel title={t("common.action_failed")} message={actionError} />}
      <div className="run-controls">
        {confirmClear ? (
          <>
            <span>{t("history.confirm_clear")}</span>
            <button type="button" className="primary" onClick={clear}>
              {t("history.clear")}
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirmClear(false);
              }}
            >
              {t("common.cancel")}
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => {
              setConfirmClear(true);
            }}
          >
            {t("history.clear")}
          </button>
        )}
      </div>
    </>
  );
}

export interface HistoryRowProps {
  entry: HistoryEntry;
  onOpen: (path: string) => void;
  onRerun: (entry: HistoryEntry) => void;
  onRemove: (entry: HistoryEntry) => void;
}

export function HistoryRow({ entry, onOpen, onRerun, onRemove }: HistoryRowProps) {
  const output = lastOutput(entry);
  const [confirmRemove, setConfirmRemove] = useState(false);
  return (
    <li className="history-item">
      <div className="history-main">
        <span className={`run-status ${entry.status}`}>{t(STATUS_LABELS[entry.status])}</span>
        <strong>{entry.module_name}</strong>
        <span className="muted">
          {describeStart(entry.started_at)} · {describeDuration(entry.duration_ms)}
        </span>
      </div>
      <span className="history-summary">{entry.error ?? entry.summary}</span>
      {entry.warnings.length > 0 && (
        <details className="history-warnings">
          <summary className="muted">
            {plural(entry.warnings.length, t("history.warnings.one"), t("history.warnings.other"))}
          </summary>
          <ul>
            {entry.warnings.map((warning, index) => (
              <li key={index}>
                <span>
                  {warning.location && <span className="anomaly-location">{warning.location}</span>}
                  {warning.message}
                </span>
                {warning.file && (
                  <span className="log-meta" title={warning.file}>
                    {fileName(warning.file)}
                  </span>
                )}
                {warning.hint && <span className="log-meta">{warning.hint}</span>}
              </li>
            ))}
          </ul>
        </details>
      )}
      <div className="history-actions">
        {output !== null && (
          <button
            type="button"
            className="primary"
            onClick={() => {
              onOpen(output);
            }}
          >
            {t("history.open_output")}
          </button>
        )}
        <button
          type="button"
          onClick={() => {
            onRerun(entry);
          }}
        >
          {t("history.rerun")}
        </button>
        {confirmRemove ? (
          <>
            <span>{t("history.confirm_remove")}</span>
            <button
              type="button"
              className="primary"
              onClick={() => {
                setConfirmRemove(false);
                onRemove(entry);
              }}
            >
              {t("history.remove_confirm")}
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
            className="icon-button"
            aria-label={t("history.remove")}
            title={t("history.remove")}
            onClick={() => {
              setConfirmRemove(true);
            }}
          >
            <CloseIcon size={14} />
          </button>
        )}
      </div>
    </li>
  );
}

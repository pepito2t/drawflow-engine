import { Suspense, use, useEffect, useState } from "react";
import { useCommands } from "../hooks/command-registry";
import { useNotificationCenter } from "../hooks/notification-center";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { COMMANDS } from "../lib/commands";
import { toReadableError } from "../lib/error-message";
import { describeDuration, describeStart, lastOutput, type HistoryEntry } from "../lib/history";
import { clearHistory, listHistory, removeHistoryEntry } from "../lib/tauri/history";
import { openOutput } from "../lib/tauri/window";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader } from "./Spinner";

const STATUS_LABELS = { succeeded: "Terminé", failed: "Échec" } as const;

export function HistoryPanel() {
  const { id, promise, retry } = useRetryablePromise(listHistory);
  const { subscribe } = useNotificationCenter();
  useEffect(
    () =>
      subscribe((event) => {
        if (event.type === "runFinished") {
          retry();
        }
      }),
    [subscribe, retry],
  );

  return (
    <section className="module-workspace">
      <header>
        <h1>Historique</h1>
        <p>Les derniers traitements : rouvrir un résultat, relancer avec les mêmes fichiers.</p>
      </header>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <ErrorPanel
              title="Historique indisponible"
              message={message}
              hint={hint}
              onRetry={retry}
            />
          );
        }}
      >
        <Suspense fallback={<Loader label="Chargement de l'historique…" />}>
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
    clearHistory().then(onChanged).catch(fail);
  };

  if (entries.length === 0) {
    return <p className="muted">Aucun traitement pour l'instant. Lancez une fonctionnalité.</p>;
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
      {actionError && <ErrorPanel title="Action impossible" message={actionError} />}
      <div>
        <button type="button" onClick={clear}>
          Vider l'historique
        </button>
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
  return (
    <li className="history-item">
      <div className="history-main">
        <span className={`run-status ${entry.status}`}>{STATUS_LABELS[entry.status]}</span>
        <strong>{entry.module_name}</strong>
        <span className="muted">
          {describeStart(entry.started_at)} · {describeDuration(entry.duration_ms)}
        </span>
      </div>
      <span className="history-summary">{entry.error ?? entry.summary}</span>
      {entry.warnings.length > 0 && (
        <details className="history-warnings">
          <summary className="muted">
            {String(entry.warnings.length)} avertissement{entry.warnings.length > 1 ? "s" : ""}
          </summary>
          <ul>
            {entry.warnings.map((warning, index) => (
              <li key={index}>
                <span>
                  {warning.location && <span className="anomaly-location">{warning.location}</span>}
                  {warning.message}
                </span>
                {warning.file && <span className="log-meta">{warning.file}</span>}
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
            Ouvrir le résultat
          </button>
        )}
        <button
          type="button"
          onClick={() => {
            onRerun(entry);
          }}
        >
          Relancer
        </button>
        <button
          type="button"
          className="icon-button"
          aria-label="Retirer de l'historique"
          title="Retirer de l'historique"
          onClick={() => {
            onRemove(entry);
          }}
        >
          ×
        </button>
      </div>
    </li>
  );
}

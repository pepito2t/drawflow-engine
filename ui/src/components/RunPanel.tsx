import { useState } from "react";
import type { TableEvent } from "../lib/events";
import { anomaliesAsText, groupAnomalies, type AnomalyGroup } from "../lib/anomalies";
import { STATUS_LABELS } from "../lib/run-labels";
import { isPreview, type LogEntry, type RunState } from "../lib/run-state";
import { TablePreview } from "./TablePreview";
import { ErrorPanel } from "./ErrorPanel";
import { Spinner } from "./Spinner";

interface RunPanelProps {
  state: RunState;
  onStart: () => void;
  onExport: () => void;
  onCancel: () => void;
}

export function RunPanel({ state, onStart, onExport, onCancel }: RunPanelProps) {
  const isRunning = state.status === "running";
  const [dismissedTable, setDismissedTable] = useState<TableEvent | null>(null);
  const preview = isPreview(state) && state.table !== dismissedTable ? state.table : null;

  return (
    <section className="run-panel">
      <div className="run-controls">
        {isRunning ? (
          <button type="button" onClick={onCancel} disabled={state.cancelRequested}>
            {state.cancelRequested ? "Annulation…" : "Annuler"}
          </button>
        ) : (
          <button type="button" className="primary" onClick={onStart}>
            Lancer
          </button>
        )}
        <span className={`run-status ${state.status}`}>
          {isRunning && <Spinner label="Traitement en cours" />}
          {STATUS_LABELS[state.status]}
        </span>
      </div>
      {isRunning && <RunProgress state={state} />}
      {preview ? (
        <TablePreview
          table={preview}
          onExport={onExport}
          onDismiss={() => {
            setDismissedTable(preview);
          }}
        />
      ) : (
        <RunOutcome state={state} />
      )}
      {!isRunning && <AnomaliesReport groups={groupAnomalies(state.log)} />}
      {state.log.length > 0 && (
        <RunLog entries={state.log.filter((entry) => entry.level !== "warning")} />
      )}
    </section>
  );
}

function RunProgress({ state }: { state: RunState }) {
  const { progress } = state;
  return (
    <div className="progress">
      {progress ? (
        <progress value={progress.current} max={progress.total} />
      ) : (
        <progress aria-label="Démarrage" />
      )}
      <span className="muted">
        {progress
          ? `${String(progress.current)}/${String(progress.total)} · ${progress.message}`
          : "Démarrage…"}
      </span>
    </div>
  );
}

function RunOutcome({ state }: { state: RunState }) {
  if (state.status === "failed") {
    const firstError = state.log.find((entry) => entry.level === "error");
    return (
      <ErrorPanel
        title="Le traitement a échoué"
        message={firstError?.message ?? "Erreur inconnue."}
        file={firstError?.file ?? null}
        hint={firstError?.hint ?? null}
      />
    );
  }
  if (state.status !== "succeeded") {
    return null;
  }
  return (
    <div className="success-panel" role="status">
      <strong>{state.summary ?? "Traitement terminé."}</strong>
      {state.outputs.length > 0 && (
        <ul className="outputs">
          {state.outputs.map((output) => (
            <li key={output}>
              <code>{output}</code>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const COPIED_FEEDBACK_MS = 1500;

/** Every anomaly of the run, by file: what is off, where, and what to do. */
function AnomaliesReport({ groups }: { groups: AnomalyGroup[] }) {
  const [copied, setCopied] = useState(false);
  const count = groups.reduce((total, group) => total + group.items.length, 0);
  if (count === 0) {
    return null;
  }
  const copy = () => {
    navigator.clipboard
      .writeText(anomaliesAsText(groups))
      .then(() => {
        setCopied(true);
        setTimeout(() => {
          setCopied(false);
        }, COPIED_FEEDBACK_MS);
      })
      .catch((error: unknown) => {
        console.error("Avertissements non copiés :", error);
      });
  };
  return (
    <section className="anomalies" aria-label="Avertissements">
      <div className="anomalies-header">
        <strong>
          {String(count)} avertissement{count > 1 ? "s" : ""} à vérifier
        </strong>
        <button type="button" onClick={copy}>
          {copied ? "Copié" : "Copier"}
        </button>
      </div>
      {groups.map((group) => (
        <div key={group.file ?? ""} className="anomalies-group">
          <span className="anomalies-file" title={group.file ?? undefined}>
            {group.fileName}
          </span>
          <ul>
            {group.items.map((item) => (
              <li key={item.id}>
                <span>
                  {item.location && <span className="anomaly-location">{item.location}</span>}
                  {item.message}
                </span>
                {item.hint && <span className="log-meta">{item.hint}</span>}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function RunLog({ entries }: { entries: LogEntry[] }) {
  return (
    <details className="run-log" open>
      <summary>Journal ({entries.length})</summary>
      <ol>
        {entries.map((entry) => (
          <li key={entry.id} className={`log-entry ${entry.level}`}>
            <span>{entry.message}</span>
            {entry.file && <span className="log-meta">Fichier : {entry.file}</span>}
            {entry.hint && <span className="log-meta">{entry.hint}</span>}
          </li>
        ))}
      </ol>
    </details>
  );
}

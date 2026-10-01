import type { LogEntry, RunState } from "../lib/run-state";
import { ErrorPanel } from "./ErrorPanel";
import { Spinner } from "./Spinner";

interface RunPanelProps {
  state: RunState;
  onStart: () => void;
  onCancel: () => void;
}

const STATUS_LABELS: Record<RunState["status"], string> = {
  idle: "Prêt",
  running: "En cours",
  succeeded: "Terminé",
  failed: "Échec",
  cancelled: "Annulé",
};

export function RunPanel({ state, onStart, onCancel }: RunPanelProps) {
  const isRunning = state.status === "running";

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
      <RunOutcome state={state} />
      {state.log.length > 0 && <RunLog entries={state.log} />}
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

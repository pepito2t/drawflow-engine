import { plural } from "../i18n";
import { t } from "../i18n/shell";
import { t as panelText } from "../i18n/panels";
import { useState } from "react";
import { useThrottledValue } from "../hooks/use-throttled-value";
import type { TableEvent } from "../lib/events";
import { anomaliesAsText, groupAnomalies, type AnomalyGroup } from "../lib/anomalies";
import { toReadableError } from "../lib/error-message";
import { statusLabel } from "../lib/run-labels";
import { isPreview, type LogEntry, type RunState } from "../lib/run-state";
import { openOutput } from "../lib/tauri/window";
import { TablePreview } from "./TablePreview";
import { ErrorPanel } from "./ErrorPanel";
import { Spinner } from "./Spinner";

interface RunPanelProps {
  state: RunState;
  /** Labels of the required fields still empty; the run cannot start while there are any. */
  missingFields: string[];
  onStart: () => void;
  onExport: () => void;
  onCancel: () => void;
}

export function RunPanel({ state, missingFields, onStart, onExport, onCancel }: RunPanelProps) {
  const isRunning = state.status === "running";
  const [dismissedTable, setDismissedTable] = useState<TableEvent | null>(null);
  const preview = isPreview(state) && state.table !== dismissedTable ? state.table : null;
  const isIncomplete = missingFields.length > 0;

  return (
    <section className="run-panel">
      <div className="run-controls">
        {isRunning ? (
          <button type="button" onClick={onCancel} disabled={state.cancelRequested}>
            {state.cancelRequested ? t("runPanel.cancelling") : t("runPanel.cancel")}
          </button>
        ) : (
          <button type="button" className="primary" onClick={onStart} disabled={isIncomplete}>
            {t("runPanel.start")}
          </button>
        )}
        <span className={`run-status ${state.status}`}>
          {isRunning && <Spinner label={t("runPanel.running")} />}
          {statusLabel(state.status)}
        </span>
      </div>
      {!isRunning && isIncomplete && (
        <p className="muted run-missing">
          {t("runPanel.missingFields", { fields: missingFields.join(", ") })}
        </p>
      )}
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

/** Screen readers hear the progress at a sustainable pace rather than on every file. */
const PROGRESS_ANNOUNCE_INTERVAL_MS = 3_000;

function RunProgress({ state }: { state: RunState }) {
  const { progress } = state;
  const text = progress
    ? `${String(progress.current)}/${String(progress.total)} · ${progress.message}`
    : t("runPanel.starting");
  const announced = useThrottledValue(text, PROGRESS_ANNOUNCE_INTERVAL_MS);
  return (
    <div className="progress">
      {progress ? (
        <progress value={progress.current} max={progress.total} />
      ) : (
        <progress aria-label={t("runPanel.startingLabel")} />
      )}
      <span className="muted" aria-hidden="true">
        {text}
      </span>
      <span className="sr-only" aria-live="polite">
        {announced}
      </span>
    </div>
  );
}

function RunOutcome({ state }: { state: RunState }) {
  const [openError, setOpenError] = useState<string | null>(null);
  const open = (path: string) => {
    setOpenError(null);
    openOutput(path).catch((error: unknown) => {
      setOpenError(toReadableError(error).message);
    });
  };
  if (state.status === "failed") {
    const firstError = state.log.find((entry) => entry.level === "error");
    return (
      <ErrorPanel
        title={t("runPanel.failed")}
        message={firstError?.message ?? t("runPanel.unknownError")}
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
      <strong>{state.summary ?? t("run.finished")}</strong>
      {state.outputs.length > 0 && (
        <ul className="outputs">
          {state.outputs.map((output) => (
            <li key={output}>
              <code>{output}</code>
              <button
                type="button"
                onClick={() => {
                  open(output);
                }}
              >
                {panelText("history.open_output")}
              </button>
            </li>
          ))}
        </ul>
      )}
      {openError && <ErrorPanel title={panelText("common.action_failed")} message={openError} />}
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
    <section className="anomalies" aria-label={t("runPanel.anomalies")}>
      <div className="anomalies-header">
        <strong>
          {plural(count, t("runPanel.anomalyCount.one"), t("runPanel.anomalyCount.other"))}
        </strong>
        <button type="button" onClick={copy}>
          {copied ? t("runPanel.copied") : t("runPanel.copy")}
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
      <summary>{t("runPanel.log", { count: entries.length })}</summary>
      <ol>
        {entries.map((entry) => (
          <li key={entry.id} className={`log-entry ${entry.level}`}>
            <span>{entry.message}</span>
            {entry.file && (
              <span className="log-meta">{t("runPanel.file", { file: entry.file })}</span>
            )}
            {entry.hint && <span className="log-meta">{entry.hint}</span>}
          </li>
        ))}
      </ol>
    </details>
  );
}

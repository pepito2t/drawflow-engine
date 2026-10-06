import { Suspense, use, useState } from "react";
import { useCommands } from "../hooks/command-registry";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { COMMANDS } from "../lib/commands";
import { useSetupRun } from "../hooks/use-setup-run";
import { toReadableError } from "../lib/error-message";
import { t } from "../i18n/settings";
import {
  describeSystem,
  isEngineAction,
  needsConfirmation,
  parseSetupReport,
  type EngineSetupAction,
  type SetupActionSpec,
  type SetupItem,
  type SetupReport,
  type SetupRun,
  AI_MODELS_TAB_ID,
  OPEN_MODELS_ACTION,
} from "../lib/setup";
import { openDownloadPage, runSetupAction, scanSetup } from "../lib/tauri/setup";
import { openLogsFolder } from "../lib/tauri/window";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { HelpIcon } from "./icons";
import { Loader } from "./Spinner";

const STATUS_KEYS = {
  ok: "setup.status.ok",
  missing: "setup.status.missing",
  optional: "setup.status.optional",
  update: "setup.status.update",
} as const;

function loadReport(): Promise<SetupReport> {
  return scanSetup().then(parseSetupReport);
}

export function SetupPanel({ onOpenTab }: { onOpenTab: (tabId: string) => void }) {
  const { id, promise, retry } = useRetryablePromise(loadReport);
  const { run, start } = useSetupRun("setup", retry);
  const openLogs = () => {
    openLogsFolder().catch((error: unknown) => {
      console.error("Dossier des journaux non ouvert :", error);
    });
  };
  return (
    <section className="settings-section">
      <div className="setup-header">
        <h3>{t("setup.title")}</h3>
        <div className="setup-header-actions">
          <button type="button" title={t("setup.logsHint")} onClick={openLogs}>
            {t("setup.logs")}
          </button>
          <button type="button" onClick={retry}>
            {t("setup.rescan")}
          </button>
        </div>
      </div>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <ErrorPanel
              title={t("setup.scanError")}
              message={message}
              hint={hint}
              onRetry={retry}
            />
          );
        }}
      >
        <Suspense fallback={<Loader label={t("setup.scanning")} />}>
          <SetupChecklist
            reportPromise={promise}
            run={run}
            onStart={(action) => {
              start(action, (onMessage) => runSetupAction(action, onMessage));
            }}
            onOpenTab={onOpenTab}
          />
        </Suspense>
      </ErrorBoundary>
    </section>
  );
}

interface SetupChecklistProps {
  reportPromise: Promise<SetupReport>;
  run: SetupRun;
  onStart: (action: EngineSetupAction) => void;
  onOpenTab: (tabId: string) => void;
}

function SetupChecklist({ reportPromise, run, onStart, onOpenTab }: SetupChecklistProps) {
  const report = use(reportPromise);
  const [pending, setPending] = useState<SetupActionSpec | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const isBusy = run.status === "running";

  const trigger = (action: SetupActionSpec) => {
    setPageError(null);
    if (action.id === OPEN_MODELS_ACTION) {
      onOpenTab(AI_MODELS_TAB_ID);
    } else if (!isEngineAction(action.id)) {
      openPage(action).catch((error: unknown) => {
        setPageError(toReadableError(error).message);
      });
    } else if (needsConfirmation(action.id)) {
      setPending(action);
    } else {
      onStart(action.id);
    }
  };

  return (
    <>
      <p className="muted">{describeSystem(report)}</p>
      <ul className="setup-list">
        {report.items.map((item) => (
          <SetupRow
            key={item.id}
            item={item}
            run={run}
            disabled={isBusy}
            pending={pending}
            onAction={trigger}
            onConfirm={(action) => {
              setPending(null);
              if (isEngineAction(action.id)) {
                onStart(action.id);
              }
            }}
            onCancel={() => {
              setPending(null);
            }}
          />
        ))}
      </ul>
      {pageError && <ErrorPanel title={t("setup.pageNotOpened")} message={pageError} />}
    </>
  );
}

async function openPage(action: SetupActionSpec): Promise<void> {
  if (action.url === null) {
    throw new Error(t("setup.noDownloadPage"));
  }
  await openDownloadPage(action.url);
}

interface SetupRowProps {
  item: SetupItem;
  run: SetupRun;
  disabled: boolean;
  pending: SetupActionSpec | null;
  onAction: (action: SetupActionSpec) => void;
  onConfirm: (action: SetupActionSpec) => void;
  onCancel: () => void;
}

function SetupRow({ item, run, disabled, pending, onAction, onConfirm, onCancel }: SetupRowProps) {
  const ownRun =
    run.status !== "idle" && item.actions.some((a) => a.id === run.action) ? run : null;
  const confirming = pending && item.actions.some((a) => a.id === pending.id) ? pending : null;
  return (
    <li className="setup-item">
      <span className={`setup-status ${item.status}`}>{t(STATUS_KEYS[item.status])}</span>
      <div className="setup-body">
        <div className="setup-title">
          <strong>{item.label}</strong>
          {item.help && <HelpLink topic={item.help} />}
        </div>
        <span className="muted">{item.detail}</span>
        {ownRun && <RunLine run={ownRun} />}
        {confirming && (
          <div className="setup-confirm">
            <span>
              {confirming.id === "model.pull"
                ? t("setup.confirmPull")
                : t("setup.confirmLicense", { label: item.label })}
            </span>
            <button
              type="button"
              className="primary"
              onClick={() => {
                onConfirm(confirming);
              }}
            >
              {t("setup.confirm")}
            </button>
            <button type="button" onClick={onCancel}>
              {t("setup.cancel")}
            </button>
          </div>
        )}
      </div>
      <div className="setup-actions">
        {item.actions.map((action) => (
          <button
            key={action.id}
            type="button"
            className={isEngineAction(action.id) ? "primary" : undefined}
            disabled={disabled}
            onClick={() => {
              onAction(action);
            }}
          >
            {action.label}
          </button>
        ))}
      </div>
    </li>
  );
}

function RunLine({ run }: { run: Exclude<SetupRun, { status: "idle" }> }) {
  switch (run.status) {
    case "running":
      return (
        <div className="setup-run">
          <progress value={run.percent ?? undefined} max={100} />
          <span className="muted">
            {run.message || t("setup.running")}
            {run.percent !== null && ` · ${String(run.percent)} %`}
          </span>
        </div>
      );
    case "done":
      return <span className="run-status succeeded">{run.message || t("setup.done")}</span>;
    case "failed":
      return (
        <ErrorPanel
          title={t("setup.actionError")}
          message={run.error.message}
          hint={run.error.hint}
        />
      );
  }
}

function HelpLink({ topic }: { topic: string }) {
  const { execute } = useCommands();
  return (
    <button
      type="button"
      className="icon-button"
      aria-label={t("setup.help")}
      title={t("setup.help")}
      onClick={() => {
        execute(COMMANDS.openHelp, { topic })
          .then((result) => {
            if (!result.ok) console.error(result.error);
          })
          .catch((error: unknown) => {
            console.error(error);
          });
      }}
    >
      <HelpIcon />
    </button>
  );
}

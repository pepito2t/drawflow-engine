import { useState } from "react";
import {
  fitsInMemory,
  formatSize,
  type CatalogEntry,
  type ModelCatalog,
} from "../lib/model-catalog";
import type { SetupRun } from "../lib/setup";
import { t } from "../i18n/settings";
import { ErrorPanel } from "./ErrorPanel";

interface ModelRowProps {
  model: CatalogEntry;
  catalog: ModelCatalog;
  run: SetupRun;
  disabled: boolean;
  onDownload: (model: string) => void;
  onUse: (model: string) => void;
  onRemove: (model: string) => void;
}

export function ModelRow({
  model,
  catalog,
  run,
  disabled,
  onDownload,
  onUse,
  onRemove,
}: ModelRowProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const isUsed = model.name === catalog.configured;
  const tooBig = !fitsInMemory(catalog, model);
  return (
    <li className="setup-item">
      <span className={`setup-status ${model.installed ? "ok" : "optional"}`}>
        {model.installed ? t("models.installed") : formatSize(model.size_gb)}
      </span>
      <div className="setup-body">
        <strong>
          {model.label}
          {model.name === catalog.recommended && (
            <span className="badge">{t("models.badgeRecommended")}</span>
          )}
          {isUsed && <span className="badge">{t("models.badgeUsed")}</span>}
        </strong>
        <span className="muted">
          {model.name}
          {model.description && ` — ${model.description}`}
        </span>
        {tooBig && (
          <span className="assistant-error">
            {t("models.tooBig", { memory: model.min_memory_gb ?? "" })}
          </span>
        )}
        {run.status !== "idle" && run.action === model.name && <TaskLine run={run} />}
        {confirmDelete && (
          <div className="setup-confirm">
            <span>{t("models.confirmDelete", { model: model.name })}</span>
            <button
              type="button"
              className="primary"
              onClick={() => {
                setConfirmDelete(false);
                onRemove(model.name);
              }}
            >
              {t("models.delete")}
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirmDelete(false);
              }}
            >
              {t("models.cancel")}
            </button>
          </div>
        )}
      </div>
      <div className="setup-actions">
        {!model.installed && (
          <button
            type="button"
            className="primary"
            disabled={disabled || !catalog.is_ollama}
            onClick={() => {
              onDownload(model.name);
            }}
          >
            {t("models.download")}
          </button>
        )}
        {model.installed && !isUsed && (
          <button
            type="button"
            className="primary"
            disabled={disabled}
            onClick={() => {
              onUse(model.name);
            }}
          >
            {t("models.use")}
          </button>
        )}
        {model.installed && catalog.is_ollama && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              setConfirmDelete(true);
            }}
          >
            {t("models.delete")}
          </button>
        )}
      </div>
    </li>
  );
}

export function TaskLine({ run }: { run: Exclude<SetupRun, { status: "idle" }> }) {
  switch (run.status) {
    case "running":
      return (
        <div className="setup-run">
          <progress value={run.percent ?? undefined} max={100} />
          <span className="muted">
            {t("models.taskLine", {
              action: run.action,
              message: run.message || t("models.taskRunning"),
            })}
            {run.percent !== null && ` · ${String(run.percent)} %`}
          </span>
        </div>
      );
    case "done":
      return <span className="run-status succeeded">{run.message || t("models.done")}</span>;
    case "failed":
      return (
        <ErrorPanel
          title={t("models.downloadError")}
          message={run.error.message}
          hint={run.error.hint}
        />
      );
  }
}

import { useState } from "react";
import {
  fitsInMemory,
  formatSize,
  type CatalogEntry,
  type ModelCatalog,
} from "../lib/model-catalog";
import type { SetupRun } from "../lib/setup";
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
        {model.installed ? "Installé" : formatSize(model.size_gb)}
      </span>
      <div className="setup-body">
        <strong>
          {model.label}
          {model.name === catalog.recommended && <span className="badge">Recommandé</span>}
          {isUsed && <span className="badge">Utilisé</span>}
        </strong>
        <span className="muted">
          {model.name}
          {model.description && ` — ${model.description}`}
        </span>
        {tooBig && (
          <span className="assistant-error">
            Demande {model.min_memory_gb} Go de mémoire : risque d'être très lent sur ce poste.
          </span>
        )}
        {run.status !== "idle" && run.action === model.name && <TaskLine run={run} />}
        {confirmDelete && (
          <div className="setup-confirm">
            <span>Supprimer {model.name} de ce poste ?</span>
            <button
              type="button"
              className="primary"
              onClick={() => {
                setConfirmDelete(false);
                onRemove(model.name);
              }}
            >
              Supprimer
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirmDelete(false);
              }}
            >
              Annuler
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
            Télécharger
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
            Utiliser
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
            Supprimer
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
            {run.action} : {run.message || "en cours…"}
            {run.percent !== null && ` · ${String(run.percent)} %`}
          </span>
        </div>
      );
    case "done":
      return <span className="run-status succeeded">{run.message || "Terminé"}</span>;
    case "failed":
      return (
        <ErrorPanel
          title="Téléchargement impossible"
          message={run.error.message}
          hint={run.error.hint}
        />
      );
  }
}

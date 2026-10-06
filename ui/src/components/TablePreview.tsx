import { useState } from "react";
import type { TableEvent } from "../lib/events";

interface TablePreviewProps {
  table: TableEvent;
  onExport: () => void;
  onDismiss: () => void;
}

/** The rows about to be exported; flagged rows carry their issues as a tooltip. */
export function TablePreview({ table, onExport, onDismiss }: TablePreviewProps) {
  const [onlyIssues, setOnlyIssues] = useState(false);
  const flagged = table.rows.filter((row) => row.issues.length > 0).length;
  const rows = onlyIssues ? table.rows.filter((row) => row.issues.length > 0) : table.rows;
  const truncated = table.total - table.rows.length;

  return (
    <section className="table-preview" aria-label="Aperçu avant export">
      <div className="table-preview-header">
        <strong>
          Aperçu : {String(table.total)} ligne{table.total > 1 ? "s" : ""}
          {flagged > 0 && ` · ${String(flagged)} à vérifier`}
        </strong>
        {flagged > 0 && (
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={onlyIssues}
              onChange={(event) => {
                setOnlyIssues(event.target.checked);
              }}
            />
            Anomalies seulement
          </label>
        )}
      </div>
      <div className="table-preview-scroll">
        <table>
          <thead>
            <tr>
              {table.headers.map((header) => (
                <th key={header}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr
                key={index}
                className={row.issues.length > 0 ? "flagged" : undefined}
                title={row.issues.join(" · ") || undefined}
              >
                {row.cells.map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {truncated > 0 && (
        <span className="muted">
          {String(truncated)} ligne{truncated > 1 ? "s" : ""} de plus dans le fichier exporté.
        </span>
      )}
      <div className="run-controls">
        <button type="button" className="primary" onClick={onExport}>
          Exporter
        </button>
        <button type="button" onClick={onDismiss}>
          Annuler
        </button>
      </div>
    </section>
  );
}

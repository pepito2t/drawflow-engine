import { plural } from "../i18n";
import { t } from "../i18n/shell";
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
    <section className="table-preview" aria-label={t("tablePreview.title")}>
      <div className="table-preview-header">
        <strong>
          {plural(table.total, t("tablePreview.rows.one"), t("tablePreview.rows.other"))}
          {flagged > 0 && ` · ${t("tablePreview.flagged", { count: flagged })}`}
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
            {t("tablePreview.onlyIssues")}
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
          {plural(truncated, t("tablePreview.truncated.one"), t("tablePreview.truncated.other"))}
        </span>
      )}
      <div className="run-controls">
        <button type="button" className="primary" onClick={onExport}>
          {t("tablePreview.export")}
        </button>
        <button type="button" onClick={onDismiss}>
          {t("tablePreview.cancel")}
        </button>
      </div>
    </section>
  );
}

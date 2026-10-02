import { useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { toReadableError, type ReadableError } from "../lib/error-message";
import type { FormValues } from "../lib/form-schema";
import type { SettingsSection } from "../lib/settings";
import {
  importedFormValues,
  SETTINGS_FILE_FILTERS,
  SETTINGS_FILE_SUFFIX,
} from "../lib/settings-transfer";
import { pickPaths, pickSavePath } from "../lib/tauri/dialog";
import { engineRequest } from "../lib/tauri/engine";
import { ErrorPanel } from "./ErrorPanel";

interface SectionTransferProps {
  section: SettingsSection;
  disabled: boolean;
  onImported: (values: FormValues) => void;
}

export function SectionTransfer({ section, disabled, onImported }: SectionTransferProps) {
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<ReadableError | null>(null);
  const { publish } = useNotificationCenter();

  const fail = (reason: unknown) => {
    setError(toReadableError(reason));
  };

  const exportSection = () => {
    setError(null);
    pickSavePath({
      title: `Exporter « ${section.title} »`,
      defaultPath: `${section.title}${SETTINGS_FILE_SUFFIX}`,
      filters: SETTINGS_FILE_FILTERS,
    })
      .then(async (target) => {
        if (target === null) {
          return;
        }
        await engineRequest("settings.export", { section: section.id, target });
        publish({ type: "settingsExported", target });
      })
      .catch(fail);
  };

  const importSection = () => {
    setError(null);
    pickPaths({
      directory: false,
      multiple: false,
      title: "Importer des paramètres",
      filters: SETTINGS_FILE_FILTERS,
    })
      .then(async ([source]) => {
        if (source === undefined) {
          return;
        }
        onImported(
          importedFormValues(await engineRequest("settings.read-import", { source }), section),
        );
        setNotice("Valeurs importées : vérifiez-les puis cliquez sur « Enregistrer ».");
      })
      .catch(fail);
  };

  return (
    <div className="section-transfer">
      <div className="run-controls">
        <button type="button" disabled={disabled} onClick={importSection}>
          Importer…
        </button>
        <button type="button" disabled={disabled} onClick={exportSection}>
          Exporter…
        </button>
        {notice && <span className="muted">{notice}</span>}
      </div>
      {error && (
        <ErrorPanel
          title="Import / export impossible"
          message={error.message}
          hint={error.hint}
          file={error.file}
        />
      )}
    </div>
  );
}

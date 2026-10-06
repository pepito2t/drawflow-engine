import { useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { toReadableError, type ReadableError } from "../lib/error-message";
import { t } from "../i18n/settings";
import type { FormValues } from "../lib/form-schema";
import type { SettingsSection } from "../lib/settings";
import {
  importedFormValues,
  settingsFileFilters,
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
      title: t("transfer.exportTitle", { title: section.title }),
      defaultPath: `${section.title}${SETTINGS_FILE_SUFFIX}`,
      filters: settingsFileFilters(),
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
      title: t("transfer.importTitle"),
      filters: settingsFileFilters(),
    })
      .then(async ([source]) => {
        if (source === undefined) {
          return;
        }
        onImported(
          importedFormValues(await engineRequest("settings.read-import", { source }), section),
        );
        setNotice(t("transfer.imported"));
      })
      .catch(fail);
  };

  return (
    <div className="section-transfer">
      <div className="run-controls">
        <button type="button" disabled={disabled} onClick={importSection}>
          {t("transfer.import")}
        </button>
        <button type="button" disabled={disabled} onClick={exportSection}>
          {t("transfer.export")}
        </button>
        {notice && <span className="muted">{notice}</span>}
      </div>
      {error && (
        <ErrorPanel
          title={t("transfer.error")}
          message={error.message}
          hint={error.hint}
          file={error.file}
        />
      )}
    </div>
  );
}

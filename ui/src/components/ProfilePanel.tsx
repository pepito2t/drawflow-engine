import { useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { usePresets } from "../hooks/presets-context";
import { toReadableError, type ReadableError } from "../lib/error-message";
import { t } from "../i18n/settings";
import {
  describeProfileChanges,
  parseProfilePreview,
  profileFileFilters,
  PROFILE_FILE_SUFFIX,
  type ProfilePreview,
} from "../lib/profile";
import { pickPaths, pickSavePath } from "../lib/tauri/dialog";
import { engineRequest } from "../lib/tauri/engine";
import { ErrorPanel } from "./ErrorPanel";
import { Spinner } from "./Spinner";
import { dateLocale } from "../i18n/panels";

interface PendingImport {
  source: string;
  preview: ProfilePreview;
}

export function ProfilePanel({ onImported }: { onImported: () => void }) {
  const { publish } = useNotificationCenter();
  const { reload } = usePresets();
  const [pending, setPending] = useState<PendingImport | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<ReadableError | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  const fail = (reason: unknown) => {
    setError(toReadableError(reason));
    setIsBusy(false);
  };

  const exportProfile = () => {
    setError(null);
    setNotice(null);
    pickSavePath({
      title: t("profile.exportTitle"),
      defaultPath: `${t("profile.defaultFileName")}${PROFILE_FILE_SUFFIX}`,
      filters: profileFileFilters(),
    })
      .then(async (target) => {
        if (target === null) {
          return;
        }
        setIsBusy(true);
        await engineRequest("profile.export", { target });
        publish({ type: "settingsExported", target });
        setNotice(t("profile.exported"));
        setIsBusy(false);
      })
      .catch(fail);
  };

  const chooseProfile = () => {
    setError(null);
    setNotice(null);
    pickPaths({
      directory: false,
      multiple: false,
      title: t("profile.importTitle"),
      filters: profileFileFilters(),
    })
      .then(async ([source]) => {
        if (source === undefined) {
          return;
        }
        setIsBusy(true);
        const preview = parseProfilePreview(await engineRequest("profile.read-import", { source }));
        setPending({ source, preview });
        setIsBusy(false);
      })
      .catch(fail);
  };

  const applyProfile = () => {
    if (!pending) {
      return;
    }
    setIsBusy(true);
    setError(null);
    engineRequest("profile.import", { source: pending.source })
      .then(reload)
      .then(() => {
        setPending(null);
        setNotice(t("profile.applied"));
        setIsBusy(false);
        publish({ type: "settingsSaved" });
        onImported();
      })
      .catch(fail);
  };

  return (
    <section className="settings-section">
      <h3>{t("profile.title")}</h3>
      <p className="muted">{t("profile.intro")}</p>
      <div className="run-controls">
        <button type="button" disabled={isBusy} onClick={exportProfile}>
          {t("profile.export")}
        </button>
        <button type="button" disabled={isBusy} onClick={chooseProfile}>
          {t("profile.import")}
        </button>
        {isBusy && <Spinner label={t("profile.busy")} />}
        {notice && <span className="run-status succeeded">{notice}</span>}
      </div>
      {pending && (
        <div className="profile-preview">
          <p>
            {t("profile.previewOf", { version: pending.preview.app_version })}
            {pending.preview.exported_at &&
              t("profile.previewExportedAt", {
                date: new Date(pending.preview.exported_at).toLocaleDateString(dateLocale()),
              })}
            {t("profile.previewReplaces")}
          </p>
          <ul>
            {describeProfileChanges(pending.preview).map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <div className="run-controls">
            <button type="button" className="primary" disabled={isBusy} onClick={applyProfile}>
              {t("profile.apply")}
            </button>
            <button
              type="button"
              disabled={isBusy}
              onClick={() => {
                setPending(null);
              }}
            >
              {t("profile.cancel")}
            </button>
          </div>
        </div>
      )}
      {error && (
        <ErrorPanel
          title={t("profile.notApplied")}
          message={error.message}
          hint={error.hint}
          file={error.file}
        />
      )}
    </section>
  );
}

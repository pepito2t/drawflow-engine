import { useState } from "react";
import { useNotificationCenter } from "../hooks/notification-center";
import { usePresets } from "../hooks/presets-context";
import { toReadableError, type ReadableError } from "../lib/error-message";
import {
  describeProfileChanges,
  parseProfilePreview,
  PROFILE_FILE_FILTERS,
  PROFILE_FILE_SUFFIX,
  type ProfilePreview,
} from "../lib/profile";
import { pickPaths, pickSavePath } from "../lib/tauri/dialog";
import { engineRequest } from "../lib/tauri/engine";
import { ErrorPanel } from "./ErrorPanel";
import { Spinner } from "./Spinner";

const DEFAULT_FILE_NAME = `Profil Drawflow${PROFILE_FILE_SUFFIX}`;

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
      title: "Exporter le profil",
      defaultPath: DEFAULT_FILE_NAME,
      filters: PROFILE_FILE_FILTERS,
    })
      .then(async (target) => {
        if (target === null) {
          return;
        }
        setIsBusy(true);
        await engineRequest("profile.export", { target });
        publish({ type: "settingsExported", target });
        setNotice("Profil exporté.");
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
      title: "Importer un profil",
      filters: PROFILE_FILE_FILTERS,
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
        setNotice("Profil appliqué.");
        setIsBusy(false);
        publish({ type: "settingsSaved" });
        onImported();
      })
      .catch(fail);
  };

  return (
    <section className="settings-section">
      <h3>Profil</h3>
      <p className="muted">
        Le profil réunit toutes les normes, les modèles Excel et Word importés et les préréglages.
        Exportez-le pour installer un autre poste à l'identique. Le code d'accès et le jeton de
        l'API locale n'en font pas partie.
      </p>
      <div className="run-controls">
        <button type="button" disabled={isBusy} onClick={exportProfile}>
          Exporter le profil…
        </button>
        <button type="button" disabled={isBusy} onClick={chooseProfile}>
          Importer un profil…
        </button>
        {isBusy && <Spinner label="Profil en cours" />}
        {notice && <span className="run-status succeeded">{notice}</span>}
      </div>
      {pending && (
        <div className="profile-preview">
          <p>
            Profil de Drawflow {pending.preview.app_version}
            {pending.preview.exported_at &&
              `, exporté le ${new Date(pending.preview.exported_at).toLocaleDateString("fr-CH")}`}
            . Appliquer remplace :
          </p>
          <ul>
            {describeProfileChanges(pending.preview).map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <div className="run-controls">
            <button type="button" className="primary" disabled={isBusy} onClick={applyProfile}>
              Appliquer le profil
            </button>
            <button
              type="button"
              disabled={isBusy}
              onClick={() => {
                setPending(null);
              }}
            >
              Annuler
            </button>
          </div>
        </div>
      )}
      {error && (
        <ErrorPanel
          title="Profil non appliqué"
          message={error.message}
          hint={error.hint}
          file={error.file}
        />
      )}
    </section>
  );
}

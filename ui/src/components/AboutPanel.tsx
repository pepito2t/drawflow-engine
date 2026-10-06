import { Suspense, use } from "react";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { toReadableError } from "../lib/error-message";
import { formatSavedTime, totalsOf, type UsageStats } from "../lib/stats";
import { getAppVersion } from "../lib/tauri/app";
import { getUsageStats } from "../lib/tauri/history";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader } from "./Spinner";

interface AboutData {
  version: string;
  stats: UsageStats;
}

function loadAbout(): Promise<AboutData> {
  return Promise.all([getAppVersion(), getUsageStats()]).then(([version, stats]) => ({
    version,
    stats,
  }));
}

export function AboutPanel({ onOpenGeneral }: { onOpenGeneral: () => void }) {
  const { id, promise, retry } = useRetryablePromise(loadAbout);
  return (
    <ErrorBoundary
      key={id}
      fallback={(error) => {
        const { message, hint, file } = toReadableError(error);
        return (
          <ErrorPanel
            title="Compteurs indisponibles"
            message={message}
            hint={hint}
            file={file}
            onRetry={retry}
          />
        );
      }}
    >
      <Suspense fallback={<Loader label="Chargement…" />}>
        <AboutContent dataPromise={promise} onOpenGeneral={onOpenGeneral} />
      </Suspense>
    </ErrorBoundary>
  );
}

interface AboutContentProps {
  dataPromise: Promise<AboutData>;
  onOpenGeneral: () => void;
}

function AboutContent({ dataPromise, onOpenGeneral }: AboutContentProps) {
  const { version, stats } = use(dataPromise);
  const totals = totalsOf(stats);
  const since = stats.since ? new Date(stats.since).toLocaleDateString("fr-CH") : null;
  return (
    <section className="settings-section">
      <h3>À propos</h3>
      <p className="muted">Drawflow {version}</p>
      <h4>Ce que Drawflow a fait sur ce poste</h4>
      {stats.features.length === 0 ? (
        <p className="muted">Aucun traitement terminé pour l'instant.</p>
      ) : (
        <table className="stats-table">
          <thead>
            <tr>
              <th>Fonctionnalité</th>
              <th>Traitements</th>
              <th>Fichiers</th>
              <th>Temps gagné</th>
            </tr>
          </thead>
          <tbody>
            {stats.features.map((feature) => (
              <tr key={feature.module}>
                <td>{feature.module_name}</td>
                <td>{feature.runs}</td>
                <td>{feature.files}</td>
                <td>{formatSavedTime(feature.minutes_saved)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td>Total{since && ` depuis le ${since}`}</td>
              <td>{totals.runs}</td>
              <td>{totals.files}</td>
              <td>{formatSavedTime(totals.minutes_saved)}</td>
            </tr>
          </tfoot>
        </table>
      )}
      <p className="muted">
        Le temps gagné est une estimation : minutes par fichier réglables dans{" "}
        <button type="button" className="link-button" onClick={onOpenGeneral}>
          Général
        </button>
        , où les compteurs se désactivent. Ces chiffres restent sur ce poste.
      </p>
    </section>
  );
}

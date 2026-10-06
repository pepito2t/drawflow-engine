import { Suspense, use } from "react";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { toReadableError } from "../lib/error-message";
import { t } from "../i18n/settings";
import { formatSavedTime, totalsOf, type UsageStats } from "../lib/stats";
import { getAppVersion } from "../lib/tauri/app";
import { getUsageStats } from "../lib/tauri/history";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader } from "./Spinner";
import { dateLocale } from "../i18n/panels";

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
            title={t("about.unavailable")}
            message={message}
            hint={hint}
            file={file}
            onRetry={retry}
          />
        );
      }}
    >
      <Suspense fallback={<Loader label={t("about.loading")} />}>
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
  const since = stats.since ? new Date(stats.since).toLocaleDateString(dateLocale()) : null;
  return (
    <section className="settings-section">
      <h3>{t("about.title")}</h3>
      <p className="muted">Drawflow {version}</p>
      <h4>{t("about.subtitle")}</h4>
      {stats.features.length === 0 ? (
        <p className="muted">{t("about.empty")}</p>
      ) : (
        <table className="stats-table">
          <thead>
            <tr>
              <th>{t("about.feature")}</th>
              <th>{t("about.runs")}</th>
              <th>{t("about.files")}</th>
              <th>{t("about.savedTime")}</th>
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
              <td>{since ? t("about.totalSince", { date: since }) : t("about.total")}</td>
              <td>{totals.runs}</td>
              <td>{totals.files}</td>
              <td>{formatSavedTime(totals.minutes_saved)}</td>
            </tr>
          </tfoot>
        </table>
      )}
      <p className="muted">
        {t("about.estimateBefore")}{" "}
        <button type="button" className="link-button" onClick={onOpenGeneral}>
          {t("about.general")}
        </button>
        {t("about.estimateAfter")}
      </p>
    </section>
  );
}

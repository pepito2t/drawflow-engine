import { Suspense, use, useState } from "react";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { toReadableError, type ReadableError } from "../lib/error-message";
import { t } from "../i18n/settings";
import {
  getIntegrationStatus,
  updateIntegration,
  type IntegrationStatus,
} from "../lib/tauri/integrations";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { Loader, Spinner } from "./Spinner";

const MIN_PORT = 1024;
const MAX_PORT = 65535;

export function IntegrationsPanel() {
  const { id, promise, retry } = useRetryablePromise(getIntegrationStatus);
  return (
    <ErrorBoundary
      key={id}
      fallback={(error) => {
        const { message, hint } = toReadableError(error);
        return (
          <ErrorPanel
            title={t("integrations.unavailable")}
            message={message}
            hint={hint}
            onRetry={retry}
          />
        );
      }}
    >
      <Suspense fallback={<Loader label={t("integrations.loading")} />}>
        <IntegrationsEditor statusPromise={promise} />
      </Suspense>
    </ErrorBoundary>
  );
}

function IntegrationsEditor({ statusPromise }: { statusPromise: Promise<IntegrationStatus> }) {
  const [status, setStatus] = useState(use(statusPromise));
  const [port, setPort] = useState(String(status.port));
  const [showToken, setShowToken] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<ReadableError | null>(null);
  const portNumber = Number(port);
  const portValid =
    Number.isInteger(portNumber) && portNumber >= MIN_PORT && portNumber <= MAX_PORT;

  const apply = (enabled: boolean, regenerateToken = false) => {
    setIsBusy(true);
    setError(null);
    updateIntegration(enabled, portNumber, regenerateToken)
      .then(getIntegrationStatus)
      .then(setStatus)
      .catch((reason: unknown) => {
        setError(toReadableError(reason));
      })
      .finally(() => {
        setIsBusy(false);
      });
  };

  return (
    <section className="settings-section">
      <h3>{t("integrations.title")}</h3>
      <p className="muted">{t("integrations.intro")}</p>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={status.enabled}
          disabled={isBusy || !portValid}
          onChange={(event) => {
            apply(event.target.checked);
          }}
        />
        {t("integrations.enable")}
      </label>
      <div className="form-field">
        <label htmlFor="integration-port">{t("integrations.port")}</label>
        <input
          id="integration-port"
          type="number"
          value={port}
          disabled={isBusy}
          onChange={(event) => {
            setPort(event.target.value);
          }}
          onBlur={() => {
            if (portValid && portNumber !== status.port) {
              apply(status.enabled);
            }
          }}
        />
        {!portValid && (
          <small className="required">
            {t("integrations.portRange", { min: MIN_PORT, max: MAX_PORT })}
          </small>
        )}
      </div>
      <div className="form-field">
        <label htmlFor="integration-token">{t("integrations.token")}</label>
        <div className="token-row">
          <input
            id="integration-token"
            type={showToken ? "text" : "password"}
            readOnly
            value={status.token}
          />
          <button
            type="button"
            onClick={() => {
              setShowToken((shown) => !shown);
            }}
          >
            {showToken ? t("integrations.hide") : t("integrations.show")}
          </button>
          <button
            type="button"
            onClick={() => {
              navigator.clipboard.writeText(status.token).catch((reason: unknown) => {
                setError(toReadableError(reason));
              });
            }}
          >
            {t("integrations.copy")}
          </button>
          <button
            type="button"
            disabled={isBusy}
            onClick={() => {
              apply(status.enabled, true);
            }}
          >
            {t("integrations.regenerate")}
          </button>
        </div>
      </div>
      <p className={status.error ? "lock-error" : "muted"}>
        {status.error ??
          (status.address
            ? t("integrations.listening", { address: status.address })
            : t("integrations.disabled"))}
      </p>
      {isBusy && <Spinner label={t("integrations.applying")} />}
      {error && (
        <ErrorPanel
          title={t("integrations.changeError")}
          message={error.message}
          hint={error.hint}
        />
      )}
    </section>
  );
}

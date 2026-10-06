import { t } from "../i18n/shell";
import { useState, type SyntheticEvent } from "react";
import { describeBridgeError } from "../lib/tauri/engine";
import { unlock } from "../lib/tauri/access";
import { Spinner } from "./Spinner";

export function LockScreen({ onUnlocked }: { onUnlocked: () => void }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    setIsChecking(true);
    setError(null);
    unlock(code)
      .then(onUnlocked)
      .catch((reason: unknown) => {
        setError(describeBridgeError(reason));
        setCode("");
      })
      .finally(() => {
        setIsChecking(false);
      });
  };

  return (
    <div className="centered">
      <form className="lock-card" onSubmit={submit}>
        <h1>Drawflow</h1>
        <label htmlFor="access-code">{t("lock.title")}</label>
        <input
          id="access-code"
          type="password"
          inputMode="numeric"
          autoComplete="off"
          autoFocus
          value={code}
          disabled={isChecking}
          onChange={(event) => {
            setCode(event.target.value);
          }}
        />
        {error && (
          <p className="lock-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="primary" disabled={isChecking || code === ""}>
          {isChecking ? <Spinner label={t("lock.checking")} /> : t("lock.unlock")}
        </button>
      </form>
    </div>
  );
}

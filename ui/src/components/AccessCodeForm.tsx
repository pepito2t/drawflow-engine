import { useState, type SyntheticEvent } from "react";
import { accessCodeIssueMessage, checkNewAccessCode } from "../lib/access-code";
import { changeAccessCode } from "../lib/tauri/access";
import { describeBridgeError } from "../lib/tauri/engine";
import { useNotificationCenter } from "../hooks/notification-center";
import { t } from "../i18n/settings";
import { ErrorPanel } from "./ErrorPanel";
import { Spinner } from "./Spinner";

type ChangeState = { status: "idle" | "saving" | "saved" } | { status: "failed"; message: string };

const CODE_FIELDS = [
  { name: "current", label: "accessCode.current" },
  { name: "next", label: "accessCode.next" },
  { name: "confirmation", label: "accessCode.confirmation" },
] as const;

type CodeFieldName = (typeof CODE_FIELDS)[number]["name"];

const EMPTY_CODES: Record<CodeFieldName, string> = { current: "", next: "", confirmation: "" };

export function AccessCodeForm() {
  const [codes, setCodes] = useState(EMPTY_CODES);
  const [state, setState] = useState<ChangeState>({ status: "idle" });
  const { publish } = useNotificationCenter();

  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    const issue = checkNewAccessCode(codes.current, codes.next, codes.confirmation);
    if (issue) {
      setState({ status: "failed", message: accessCodeIssueMessage(issue) });
      return;
    }
    setState({ status: "saving" });
    changeAccessCode(codes.current, codes.next)
      .then(() => {
        setCodes(EMPTY_CODES);
        setState({ status: "saved" });
        publish({ type: "accessCodeChanged" });
      })
      .catch((error: unknown) => {
        setState({ status: "failed", message: describeBridgeError(error) });
      });
  };

  return (
    <form className="settings-section" onSubmit={submit}>
      <h3>{t("accessCode.title")}</h3>
      <p className="muted">{t("accessCode.intro")}</p>
      {CODE_FIELDS.map((field) => (
        <div key={field.name} className="form-field">
          <label htmlFor={`access-${field.name}`}>{t(field.label)}</label>
          <input
            id={`access-${field.name}`}
            type="password"
            inputMode="numeric"
            autoComplete="off"
            value={codes[field.name]}
            onChange={(event) => {
              setCodes((current) => ({ ...current, [field.name]: event.target.value }));
            }}
          />
        </div>
      ))}
      <div className="run-controls">
        <button type="submit" className="primary" disabled={state.status === "saving"}>
          {t("accessCode.change")}
        </button>
        {state.status === "saving" && <Spinner label={t("accessCode.saving")} />}
        {state.status === "saved" && (
          <span className="run-status succeeded">{t("accessCode.changed")}</span>
        )}
      </div>
      {state.status === "failed" && (
        <ErrorPanel title={t("accessCode.notChanged")} message={state.message} />
      )}
    </form>
  );
}

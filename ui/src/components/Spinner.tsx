import { t } from "../i18n/shell";
interface SpinnerProps {
  label?: string;
}

export function Spinner({ label }: SpinnerProps) {
  return <span className="spinner" role="status" aria-label={label ?? t("spinner.loading")} />;
}

export function Loader({ label }: { label: string }) {
  return (
    <div className="loader">
      <Spinner label={label} />
      <span>{label}</span>
    </div>
  );
}

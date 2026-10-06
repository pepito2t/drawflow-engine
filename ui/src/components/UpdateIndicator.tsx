import { t } from "../i18n/shell";
import { useUpdateCenter } from "../hooks/update-center";
import { describeUpdate } from "../lib/update-state";

export function UpdateIndicator() {
  const { state, install } = useUpdateCenter();
  const label = describeUpdate(state);

  if (state.status === "unconfigured") {
    return null;
  }
  if (state.status === "available") {
    return (
      <button
        type="button"
        className="status-update"
        title={t("updateIndicator.installTitle")}
        onClick={install}
      >
        {t("updateIndicator.install", { label })}
      </button>
    );
  }
  const title = state.status === "error" ? state.message : undefined;
  const tone = state.status === "error" ? "status-item error" : "status-item muted";
  return (
    <span className={tone} title={title}>
      {label}
    </span>
  );
}

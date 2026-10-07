import { t } from "../i18n/shell";

export type UpdateState =
  | { status: "checking" }
  | { status: "unconfigured" }
  | { status: "upToDate" }
  | { status: "available"; version: string }
  | { status: "downloading"; version: string; progress: number | null }
  | { status: "installing"; version: string }
  | { status: "error"; message: string; version: string | null };

export type UpdateAction =
  | { type: "checked"; state: UpdateState }
  | { type: "downloadStarted" }
  | { type: "progressed"; downloaded: number; total: number | null }
  | { type: "downloaded" }
  | { type: "failed"; message: string };

export function updateReducer(state: UpdateState, action: UpdateAction): UpdateState {
  switch (action.type) {
    case "checked":
      return state.status === "checking" ? action.state : state;
    case "downloadStarted": {
      const version = retryableVersion(state);
      return version === null ? state : { status: "downloading", version, progress: null };
    }
    case "progressed":
      return state.status === "downloading"
        ? {
            ...state,
            progress: action.total ? Math.min(action.downloaded / action.total, 1) : null,
          }
        : state;
    case "downloaded":
      return state.status === "downloading"
        ? { status: "installing", version: state.version }
        : state;
    case "failed":
      return {
        status: "error",
        message: action.message,
        version: "version" in state ? state.version : null,
      };
  }
}

/** A failed download or install can be retried as long as the update version is known. */
function retryableVersion(state: UpdateState): string | null {
  if (state.status === "available") {
    return state.version;
  }
  if (state.status === "error") {
    return state.version;
  }
  return null;
}

const PERCENT = 100;

export function describeUpdate(state: UpdateState): string {
  switch (state.status) {
    case "checking":
      return t("updateState.checking");
    case "unconfigured":
      return t("updateState.unconfigured");
    case "upToDate":
      return t("updateState.upToDate");
    case "available":
      return t("updateState.available", { version: state.version });
    case "downloading":
      return state.progress === null
        ? t("updateState.downloading", { version: state.version })
        : t("updateState.downloadProgress", { percent: Math.round(state.progress * PERCENT) });
    case "installing":
      return t("updateState.installing", { version: state.version });
    case "error":
      return t("updateState.error");
  }
}

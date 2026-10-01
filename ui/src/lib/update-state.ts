export type UpdateState =
  | { status: "unconfigured" }
  | { status: "upToDate" }
  | { status: "available"; version: string }
  | { status: "downloading"; version: string; progress: number | null }
  | { status: "installing"; version: string }
  | { status: "error"; message: string };

export type UpdateAction =
  | { type: "downloadStarted" }
  | { type: "progressed"; downloaded: number; total: number | null }
  | { type: "downloaded" }
  | { type: "failed"; message: string };

export function updateReducer(state: UpdateState, action: UpdateAction): UpdateState {
  switch (action.type) {
    case "downloadStarted":
      return state.status === "available"
        ? { status: "downloading", version: state.version, progress: null }
        : state;
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
      return { status: "error", message: action.message };
  }
}

const PERCENT = 100;

export function describeUpdate(state: UpdateState): string {
  switch (state.status) {
    case "unconfigured":
      return "Mises à jour : non configurées";
    case "upToDate":
      return "À jour";
    case "available":
      return `Version ${state.version} disponible`;
    case "downloading":
      return state.progress === null
        ? `Téléchargement de ${state.version}…`
        : `Téléchargement ${String(Math.round(state.progress * PERCENT))} %`;
    case "installing":
      return `Installation de ${state.version}…`;
    case "error":
      return "Mise à jour impossible";
  }
}

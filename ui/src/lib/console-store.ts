import { lastEntryId, mergeEntries, type ConsoleEntry } from "./console";

export interface ConsoleState {
  entries: ConsoleEntry[];
  /** Errors after this id count as unseen in the status bar badge. */
  lastSeenId: number;
  isPanelOpen: boolean;
  loadError: string | null;
}

export type ConsoleAction =
  | { type: "received"; entries: ConsoleEntry[] }
  | { type: "cleared" }
  | { type: "loadFailed"; message: string }
  | { type: "panelToggled" }
  | { type: "panelClosed" }
  | { type: "detached" };

export const INITIAL_CONSOLE_STATE: ConsoleState = {
  entries: [],
  lastSeenId: -1,
  isPanelOpen: false,
  loadError: null,
};

export function consoleReducer(state: ConsoleState, action: ConsoleAction): ConsoleState {
  switch (action.type) {
    case "received": {
      const entries = mergeEntries(state.entries, action.entries);
      const lastSeenId = state.isPanelOpen ? lastEntryId(entries) : state.lastSeenId;
      return { ...state, entries, lastSeenId, loadError: null };
    }
    case "cleared":
      return { ...state, entries: [] };
    case "loadFailed":
      return { ...state, loadError: action.message };
    case "panelToggled":
      return state.isPanelOpen
        ? { ...state, isPanelOpen: false }
        : { ...state, isPanelOpen: true, lastSeenId: lastEntryId(state.entries) };
    case "panelClosed":
      return { ...state, isPanelOpen: false };
    case "detached":
      return { ...state, isPanelOpen: false, lastSeenId: lastEntryId(state.entries) };
  }
}

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type MouseEvent,
} from "react";
import { t } from "../i18n/console";
import { copyForSupport } from "../hooks/console-context";
import { useLanguage } from "../hooks/use-language";
import {
  CONSOLE_DISPLAY_LIMIT,
  CONSOLE_SOURCES,
  DEFAULT_FILTER,
  EMPTY_SELECTION,
  entryOrigin,
  filterEntries,
  formatTime,
  isScrolledToBottom,
  LEVEL_FILTERS,
  selectAll,
  selectedEntries,
  selectEntry,
  toLevelFilter,
  toSourceFilter,
  type ConsoleEntry,
  type ConsoleFilter,
  type Selection,
  type SelectionMode,
} from "../lib/console";
import { describeUnknownError } from "../lib/console-capture";
import { CloseIcon } from "./icons";

const FEEDBACK_DURATION_MS = 2000;

const LEVEL_FILTER_LABELS = {
  all: "console.level.all",
  warnings: "console.level.warnings",
  errors: "console.level.errors",
} as const;

interface ConsolePanelProps {
  entries: ConsoleEntry[];
  loadError: string | null;
  onClose: () => void;
  onClear: () => Promise<void>;
  onDetach?: () => Promise<void>;
}

type FailureKey = "console.copyFailed" | "console.actionFailed";

interface Notice {
  tone: "ok" | "error";
  text: string;
}

export function ConsolePanel({
  entries,
  loadError,
  onClose,
  onClear,
  onDetach,
}: ConsolePanelProps) {
  useLanguage();
  const [filter, setFilter] = useState<ConsoleFilter>(DEFAULT_FILTER);
  const [selection, setSelection] = useState<Selection>(EMPTY_SELECTION);
  const [notice, showNotice] = useNotice();
  const filtered = useMemo(() => filterEntries(entries, filter), [entries, filter]);
  const visible = useMemo(() => filtered.slice(-CONSOLE_DISPLAY_LIMIT), [filtered]);
  const visibleIds = useMemo(() => visible.map((entry) => entry.id), [visible]);
  const selected = useMemo(() => selectedEntries(entries, selection), [entries, selection]);

  const run = useCallback(
    (action: () => Promise<void>, failureKey: FailureKey, success?: string) => {
      action()
        .then(() => {
          if (success) {
            showNotice({ tone: "ok", text: success });
          }
        })
        .catch((error: unknown) => {
          const { message } = describeUnknownError(error);
          showNotice({ tone: "error", text: t(failureKey, { message }) });
        });
    },
    [showNotice],
  );
  const copy = useCallback(
    (copied: readonly ConsoleEntry[]) => {
      run(() => copyForSupport(copied), "console.copyFailed", t("console.copied"));
    },
    [run],
  );
  const onSelect = useCallback(
    (id: number, mode: SelectionMode) => {
      setSelection((current) => selectEntry(current, id, visibleIds, mode));
    },
    [visibleIds],
  );
  const onKeyDown = (event: KeyboardEvent) => {
    const isShortcut = event.ctrlKey || event.metaKey;
    const key = event.key.toLowerCase();
    if (isShortcut && key === "a") {
      event.preventDefault();
      setSelection(selectAll(visibleIds));
    } else if (isShortcut && key === "c" && selected.length > 0 && !hasTextSelection()) {
      event.preventDefault();
      copy(selected);
    } else if (event.key === "Escape") {
      onClose();
    }
  };

  return (
    <section className="console-panel" aria-label={t("console.title")} onKeyDown={onKeyDown}>
      <div className="console-toolbar">
        <strong className="console-title">{t("console.title")}</strong>
        <ConsoleFilters filter={filter} onChange={setFilter} />
        <span className="console-spacer" />
        <ConsoleActions
          onCopySelection={
            selected.length > 0
              ? () => {
                  copy(selected);
                }
              : null
          }
          onCopyAll={
            filtered.length > 0
              ? () => {
                  copy(filtered);
                }
              : null
          }
          onClear={() => {
            setSelection(EMPTY_SELECTION);
            run(onClear, "console.actionFailed");
          }}
          onDetach={
            onDetach
              ? () => {
                  run(onDetach, "console.actionFailed");
                }
              : null
          }
          onClose={onClose}
        />
      </div>
      <ConsoleStatus
        loadError={loadError}
        notice={notice}
        isTruncated={filtered.length > visible.length}
      />
      <ConsoleList
        entries={visible}
        emptyText={entries.length === 0 ? t("console.empty") : t("console.noMatch")}
        selection={selection}
        onSelect={onSelect}
      />
    </section>
  );
}

/** Native text selection inside a row keeps the browser's own Ctrl+C behaviour. */
function hasTextSelection(): boolean {
  return Boolean(window.getSelection()?.toString());
}

interface ConsoleActionsProps {
  onCopySelection: (() => void) | null;
  onCopyAll: (() => void) | null;
  onClear: () => void;
  onDetach: (() => void) | null;
  onClose: () => void;
}

function ConsoleActions({
  onCopySelection,
  onCopyAll,
  onClear,
  onDetach,
  onClose,
}: ConsoleActionsProps) {
  return (
    <>
      <button type="button" disabled={!onCopySelection} onClick={onCopySelection ?? undefined}>
        {t("console.copySelection")}
      </button>
      <button type="button" disabled={!onCopyAll} onClick={onCopyAll ?? undefined}>
        {t("console.copyAll")}
      </button>
      <button type="button" onClick={onClear}>
        {t("console.clear")}
      </button>
      {onDetach && (
        <button type="button" onClick={onDetach}>
          {t("console.detach")}
        </button>
      )}
      <button
        type="button"
        className="icon-button"
        aria-label={t("console.close")}
        title={t("console.close")}
        onClick={onClose}
      >
        <CloseIcon size={16} />
      </button>
    </>
  );
}

function useNotice(): [Notice | null, (notice: Notice) => void] {
  const [notice, setNotice] = useState<Notice | null>(null);
  useEffect(() => {
    if (notice === null) {
      return;
    }
    const timer = window.setTimeout(() => {
      setNotice(null);
    }, FEEDBACK_DURATION_MS);
    return () => {
      window.clearTimeout(timer);
    };
  }, [notice]);
  return [notice, setNotice];
}

interface ConsoleFiltersProps {
  filter: ConsoleFilter;
  onChange: (filter: ConsoleFilter) => void;
}

function ConsoleFilters({ filter, onChange }: ConsoleFiltersProps) {
  return (
    <>
      <select
        aria-label={t("console.levelFilter")}
        value={filter.level}
        onChange={(event) => {
          onChange({ ...filter, level: toLevelFilter(event.target.value) });
        }}
      >
        {LEVEL_FILTERS.map((level) => (
          <option key={level} value={level}>
            {t(LEVEL_FILTER_LABELS[level])}
          </option>
        ))}
      </select>
      <select
        aria-label={t("console.sourceFilter")}
        value={filter.source}
        onChange={(event) => {
          onChange({ ...filter, source: toSourceFilter(event.target.value) });
        }}
      >
        <option value="all">{t("console.source.all")}</option>
        {CONSOLE_SOURCES.map((source) => (
          <option key={source} value={source}>
            {t(`console.source.${source}`)}
          </option>
        ))}
      </select>
      <input
        type="search"
        className="console-search"
        placeholder={t("console.search")}
        aria-label={t("console.search")}
        value={filter.query}
        onChange={(event) => {
          onChange({ ...filter, query: event.target.value });
        }}
      />
    </>
  );
}

interface ConsoleStatusProps {
  loadError: string | null;
  notice: Notice | null;
  isTruncated: boolean;
}

function ConsoleStatus({ loadError, notice, isTruncated }: ConsoleStatusProps) {
  if (loadError !== null) {
    return (
      <p className="console-status error" role="alert">
        {t("console.unavailable", { message: loadError })}
      </p>
    );
  }
  if (notice !== null) {
    return (
      <p className={`console-status ${notice.tone}`} role="status">
        {notice.text}
      </p>
    );
  }
  return (
    <p className="console-status muted">
      {isTruncated
        ? t("console.truncated", { count: CONSOLE_DISPLAY_LIMIT })
        : t("console.selectionHint")}
    </p>
  );
}

interface ConsoleListProps {
  entries: ConsoleEntry[];
  emptyText: string;
  selection: Selection;
  onSelect: (id: number, mode: SelectionMode) => void;
}

function ConsoleList({ entries, emptyText, selection, onSelect }: ConsoleListProps) {
  const list = useRef<HTMLUListElement>(null);
  const followsEnd = useRef(true);
  useLayoutEffect(() => {
    if (followsEnd.current && list.current) {
      list.current.scrollTop = list.current.scrollHeight;
    }
  }, [entries]);

  if (entries.length === 0) {
    return <p className="console-empty muted">{emptyText}</p>;
  }
  return (
    <ul
      ref={list}
      className="console-list"
      role="listbox"
      aria-label={t("console.list")}
      aria-multiselectable="true"
      tabIndex={0}
      onScroll={(event) => {
        const { scrollHeight, scrollTop, clientHeight } = event.currentTarget;
        followsEnd.current = isScrolledToBottom(scrollHeight, scrollTop, clientHeight);
      }}
    >
      {entries.map((entry) => (
        <ConsoleRow
          key={entry.id}
          entry={entry}
          isSelected={selection.ids.has(entry.id)}
          onSelect={onSelect}
        />
      ))}
    </ul>
  );
}

function selectionMode(event: MouseEvent): SelectionMode {
  if (event.shiftKey) {
    return "range";
  }
  return event.ctrlKey || event.metaKey ? "toggle" : "single";
}

interface ConsoleRowProps {
  entry: ConsoleEntry;
  isSelected: boolean;
  onSelect: (id: number, mode: SelectionMode) => void;
}

function ConsoleRow({ entry, isSelected, onSelect }: ConsoleRowProps) {
  return (
    <li
      role="option"
      aria-selected={isSelected}
      className={`console-row level-${entry.level}${isSelected ? " selected" : ""}`}
      onMouseDown={(event) => {
        // Shift+click would otherwise also select page text across the rows.
        if (event.shiftKey) {
          event.preventDefault();
        }
      }}
      onClick={(event) => {
        onSelect(entry.id, selectionMode(event));
      }}
    >
      <span className="console-time">{formatTime(entry.timestamp)}</span>
      <span className="console-level">{entry.level.toUpperCase()}</span>
      <span className="console-origin">{entryOrigin(entry)}</span>
      <span className="console-message">{entry.message}</span>
      {entry.detail && <pre className="console-detail">{entry.detail}</pre>}
    </li>
  );
}

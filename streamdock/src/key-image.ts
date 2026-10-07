import type { ConnectionState } from "./drawflow-client";
import { progressRatio, type RunView } from "./run-tracker";

export type KeyTone =
  "idle" | "running" | "succeeded" | "failed" | "offline" | "locked" | "refused" | "warning";

export interface KeyFace {
  tone: KeyTone;
  label: string;
  detail: string | null;
  progress: number | null;
}

const KEY_SIZE = 144;
const MAX_LABEL_CHARS = 12;
const MAX_DETAIL_CHARS = 16;
const MAX_LINES = 2;
const LABEL_LINE_HEIGHT = 22;
const DETAIL_LINE_HEIGHT = 20;
const LABEL_ALONE_Y = 66;
const LABEL_SHIFT_PER_DETAIL_LINE = 14;
const DETAIL_SINGLE_Y = 104;
const DETAIL_DOUBLE_Y = 84;
const ELLIPSIS = "…";
const PERCENT = 100;

const BACKGROUNDS: Record<KeyTone, string> = {
  idle: "#1f232b",
  running: "#1d3f7a",
  succeeded: "#1e6b3f",
  failed: "#8a2420",
  offline: "#2b2f36",
  locked: "#6b4d12",
  refused: "#5c1f3a",
  warning: "#9a5a0c",
};

/** Chooses what a key shows from the connection and the run of its feature. */
export function faceFor(connection: ConnectionState, label: string, run: RunView | null): KeyFace {
  if (connection === "offline") {
    return { tone: "offline", label, detail: "Hors ligne", progress: null };
  }
  if (connection === "locked") {
    return { tone: "locked", label, detail: "Verrouillé", progress: null };
  }
  if (connection === "refused") {
    return { tone: "refused", label, detail: "Jeton invalide", progress: null };
  }
  if (run === null) {
    return { tone: "idle", label, detail: null, progress: null };
  }
  switch (run.status) {
    case "running": {
      const progress = progressRatio(run);
      const detail = progress === null ? "En cours" : `${String(Math.round(progress * PERCENT))} %`;
      return { tone: "running", label, detail, progress };
    }
    case "succeeded":
      return { tone: "succeeded", label, detail: "Terminé", progress: null };
    case "failed":
      return { tone: "failed", label, detail: "Échec", progress: null };
    case "cancelled":
      return { tone: "idle", label, detail: "Annulé", progress: null };
    case "idle":
      return { tone: "idle", label, detail: null, progress: null };
  }
}

export function renderKey(face: KeyFace): string {
  const detailLines = face.detail ? wrap(face.detail, MAX_DETAIL_CHARS) : [];
  const labelLines = wrap(face.label, MAX_LABEL_CHARS).slice(
    0,
    MAX_LINES - Math.max(detailLines.length - 1, 0),
  );
  const labelY = LABEL_ALONE_Y - LABEL_SHIFT_PER_DETAIL_LINE * detailLines.length;
  const detailY = detailLines.length > 1 ? DETAIL_DOUBLE_Y : DETAIL_SINGLE_Y;
  const text = textLines(labelLines, "label", labelY, LABEL_LINE_HEIGHT);
  const detail = textLines(detailLines, "detail", detailY, DETAIL_LINE_HEIGHT);
  const bar =
    face.progress === null
      ? ""
      : `<rect x="16" y="118" width="112" height="8" rx="4" fill="#ffffff33"/><rect x="16" y="118" width="${String(Math.round(112 * face.progress))}" height="8" rx="4" fill="#ffffff"/>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${String(KEY_SIZE)}" height="${String(KEY_SIZE)}" viewBox="0 0 144 144"><style>.label{font:600 19px sans-serif;fill:#fff;text-anchor:middle}.detail{font:15px sans-serif;fill:#ffffffcc;text-anchor:middle}</style><rect width="144" height="144" fill="${BACKGROUNDS[face.tone]}"/>${text}${detail}${bar}</svg>`;
  return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
}

function textLines(lines: string[], className: string, firstY: number, lineHeight: number): string {
  return lines
    .map(
      (line, index) =>
        `<text x="72" y="${String(firstY + index * lineHeight)}" class="${className}">${escapeXml(line)}</text>`,
    )
    .join("");
}

/** Word-wraps on at most two lines; what does not fit ends with an ellipsis. */
function wrap(text: string, maxChars: number): string[] {
  const lines: string[] = [];
  for (const word of text.trim().split(/\s+/)) {
    const last = lines.at(-1);
    if (last !== undefined && `${last} ${word}`.length <= maxChars) {
      lines[lines.length - 1] = `${last} ${word}`;
    } else {
      lines.push(clip(word, maxChars));
    }
  }
  if (lines.length <= MAX_LINES) {
    return lines;
  }
  const kept = lines.slice(0, MAX_LINES);
  const last = kept[MAX_LINES - 1] ?? "";
  kept[MAX_LINES - 1] = last.endsWith(ELLIPSIS) ? last : clip(`${last}${ELLIPSIS}`, maxChars);
  return kept;
}

function clip(text: string, maxChars: number): string {
  return text.length > maxChars ? `${text.slice(0, maxChars - 1)}${ELLIPSIS}` : text;
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

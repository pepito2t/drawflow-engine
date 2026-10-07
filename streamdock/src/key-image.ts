import type { ConnectionState } from "./drawflow-client";
import { progressRatio, type RunView } from "./run-tracker";

export type KeyTone =
  "idle" | "running" | "succeeded" | "failed" | "offline" | "locked" | "refused";

export interface KeyFace {
  tone: KeyTone;
  label: string;
  detail: string | null;
  progress: number | null;
}

const KEY_SIZE = 144;
const MAX_LABEL_CHARS = 12;
const PERCENT = 100;

const BACKGROUNDS: Record<KeyTone, string> = {
  idle: "#1f232b",
  running: "#1d3f7a",
  succeeded: "#1e6b3f",
  failed: "#8a2420",
  offline: "#2b2f36",
  locked: "#6b4d12",
  refused: "#5c1f3a",
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
    case "idle":
      return { tone: "idle", label, detail: null, progress: null };
  }
}

export function renderKey(face: KeyFace): string {
  const lines = wrap(face.label);
  const firstLineY = face.detail ? 52 : 66;
  const text = lines
    .map(
      (line, index) =>
        `<text x="72" y="${String(firstLineY + index * 22)}" class="label">${escapeXml(line)}</text>`,
    )
    .join("");
  const detail = face.detail
    ? `<text x="72" y="104" class="detail">${escapeXml(face.detail)}</text>`
    : "";
  const bar =
    face.progress === null
      ? ""
      : `<rect x="16" y="118" width="112" height="8" rx="4" fill="#ffffff33"/><rect x="16" y="118" width="${String(Math.round(112 * face.progress))}" height="8" rx="4" fill="#ffffff"/>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${String(KEY_SIZE)}" height="${String(KEY_SIZE)}" viewBox="0 0 144 144"><style>.label{font:600 19px sans-serif;fill:#fff;text-anchor:middle}.detail{font:15px sans-serif;fill:#ffffffcc;text-anchor:middle}</style><rect width="144" height="144" fill="${BACKGROUNDS[face.tone]}"/>${text}${detail}${bar}</svg>`;
  return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
}

function wrap(label: string): string[] {
  const words = label.trim().split(/\s+/);
  const lines: string[] = [];
  for (const word of words) {
    const last = lines.at(-1);
    if (last !== undefined && `${last} ${word}`.length <= MAX_LABEL_CHARS) {
      lines[lines.length - 1] = `${last} ${word}`;
    } else {
      lines.push(word.length > MAX_LABEL_CHARS ? `${word.slice(0, MAX_LABEL_CHARS - 1)}…` : word);
    }
  }
  return lines.slice(0, 2);
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

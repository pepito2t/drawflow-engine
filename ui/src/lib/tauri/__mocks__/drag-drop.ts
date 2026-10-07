import type { FileDrop } from "../drag-drop";

const listeners = new Set<(drop: FileDrop) => void>();

export function listenToFileDrops(onDrop: (drop: FileDrop) => void): Promise<() => void> {
  listeners.add(onDrop);
  return Promise.resolve(() => {
    listeners.delete(onDrop);
  });
}

export function dropFiles(drop: FileDrop): void {
  for (const listener of listeners) {
    listener(drop);
  }
}

export function dropListenerCount(): number {
  return listeners.size;
}

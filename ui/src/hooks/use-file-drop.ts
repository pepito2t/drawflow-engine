import { useEffect } from "react";
import { listenToFileDrops } from "../lib/tauri/drag-drop";

const DROP_FIELD_ATTRIBUTE = "data-drop-field";

const FIELD_SEPARATOR = ":";

// Tabs stay mounted, so drop targets are namespaced by module to avoid field name collisions.
export const dropFieldProps = (moduleId: string, fieldName: string) => ({
  [DROP_FIELD_ATTRIBUTE]: `${moduleId}${FIELD_SEPARATOR}${fieldName}`,
});

export function useFileDrop(
  moduleId: string,
  onDrop: (fieldName: string, paths: string[]) => void,
): void {
  useEffect(() => {
    let unlisten: (() => void) | null = null;
    let disposed = false;
    listenToFileDrops(({ paths, x, y }) => {
      const target = dropTargetAt(x, y);
      const prefix = `${moduleId}${FIELD_SEPARATOR}`;
      if (target?.startsWith(prefix)) {
        onDrop(target.slice(prefix.length), paths);
      }
    })
      .then((stop) => {
        if (disposed) {
          stop();
        } else {
          unlisten = stop;
        }
      })
      .catch((error: unknown) => {
        console.error("Glisser-déposer indisponible :", error);
      });
    return () => {
      disposed = true;
      unlisten?.();
    };
  }, [moduleId, onDrop]);
}

function dropTargetAt(x: number, y: number): string | null {
  const target = document.elementFromPoint(x, y)?.closest(`[${DROP_FIELD_ATTRIBUTE}]`);
  return target?.getAttribute(DROP_FIELD_ATTRIBUTE) ?? null;
}

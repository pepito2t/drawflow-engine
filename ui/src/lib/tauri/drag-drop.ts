import { getCurrentWebview } from "@tauri-apps/api/webview";

export interface FileDrop {
  paths: string[];
  x: number;
  y: number;
}

export async function listenToFileDrops(onDrop: (drop: FileDrop) => void): Promise<() => void> {
  const webview = getCurrentWebview();
  const scaleFactor = await webview.window.scaleFactor();
  return webview.onDragDropEvent(({ payload }) => {
    if (payload.type !== "drop") {
      return;
    }
    const position = payload.position.toLogical(scaleFactor);
    onDrop({ paths: payload.paths, x: position.x, y: position.y });
  });
}

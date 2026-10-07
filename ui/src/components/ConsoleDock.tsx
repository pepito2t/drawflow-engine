import { useRef, useState, type PointerEvent } from "react";
import { t } from "../i18n/console";
import { useOptionalConsole } from "../hooks/console-context";
import { clampDockHeight, DEFAULT_DOCK_HEIGHT } from "../lib/console";
import { ConsolePanel } from "./ConsolePanel";

/** The console anchored above the status bar, once the app is unlocked. */
export function ConsoleDock() {
  const consoleLog = useOptionalConsole();
  const [height, setHeight] = useState(DEFAULT_DOCK_HEIGHT);
  if (!consoleLog?.isPanelOpen) {
    return null;
  }
  return (
    <div className="console-dock" style={{ height }}>
      <ResizeHandle height={height} onResize={setHeight} />
      <ConsolePanel
        entries={consoleLog.entries}
        loadError={consoleLog.loadError}
        onClose={consoleLog.closePanel}
        onClear={consoleLog.clear}
        onDetach={consoleLog.detach}
      />
    </div>
  );
}

interface ResizeHandleProps {
  height: number;
  onResize: (height: number) => void;
}

function ResizeHandle({ height, onResize }: ResizeHandleProps) {
  const drag = useRef<{ startY: number; startHeight: number } | null>(null);
  const onPointerMove = (event: PointerEvent) => {
    if (drag.current === null) {
      return;
    }
    const wanted = drag.current.startHeight + drag.current.startY - event.clientY;
    onResize(clampDockHeight(wanted, window.innerHeight));
  };
  return (
    <div
      className="console-resize"
      role="separator"
      aria-orientation="horizontal"
      aria-label={t("console.resize")}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        drag.current = { startY: event.clientY, startHeight: height };
      }}
      onPointerMove={onPointerMove}
      onPointerUp={() => {
        drag.current = null;
      }}
      onPointerCancel={() => {
        drag.current = null;
      }}
    />
  );
}

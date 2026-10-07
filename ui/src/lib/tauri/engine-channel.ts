import { Channel } from "@tauri-apps/api/core";
import { engineMessageDrafts, invalidMessageDraft, type ConsoleOrigin } from "../console-capture";
import {
  channelListener,
  type EngineMessageHandler,
  type InvalidMessageHandler,
} from "../engine-message";
import { recordConsoleEntry } from "./console";

/** Each engine message also feeds the console, tagged with who started the process. */
export function engineChannel(
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
  origin: ConsoleOrigin,
): Channel {
  return new Channel(
    channelListener(
      (message) => {
        engineMessageDrafts(message, origin).forEach(recordConsoleEntry);
        onMessage(message);
      },
      (invalid) => {
        recordConsoleEntry(invalidMessageDraft(origin, invalid));
        onInvalid(invalid);
      },
    ),
  );
}

import { Channel } from "@tauri-apps/api/core";
import {
  channelListener,
  type EngineMessageHandler,
  type InvalidMessageHandler,
} from "../engine-message";

export function engineChannel(
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): Channel {
  return new Channel(channelListener(onMessage, onInvalid));
}

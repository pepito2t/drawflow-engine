import { invoke } from "@tauri-apps/api/core";
import type { ConversationMessage } from "../assistant-chat";
import type { EngineMessageHandler, InvalidMessageHandler } from "../engine-message";
import { engineRequest } from "./engine";
import { engineChannel } from "./engine-channel";

export function startAssistantChat(
  messages: ConversationMessage[],
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): Promise<void> {
  const onEvent = engineChannel(onMessage, onInvalid);
  return invoke<undefined>("assistant_chat", { conversation: { messages }, onEvent });
}

export function cancelAssistant(): Promise<void> {
  return invoke<undefined>("assistant_cancel");
}

export function getAssistantModels(): Promise<string> {
  return engineRequest("assistant.models");
}

export function getAssistantHistory(): Promise<string> {
  return engineRequest("assistant.history-get");
}

export async function saveAssistantHistory(messages: ConversationMessage[]): Promise<void> {
  await engineRequest("assistant.history-save", { messages });
}

export function getModelCatalog(): Promise<string> {
  return engineRequest("assistant.catalog");
}

export async function deleteModel(model: string): Promise<void> {
  await engineRequest("assistant.model-delete", { model });
}

export function pullModel(
  model: string,
  onMessage: EngineMessageHandler,
  onInvalid: InvalidMessageHandler,
): Promise<string> {
  const onEvent = engineChannel(onMessage, onInvalid);
  return invoke<string>("pull_model", { model, onEvent });
}

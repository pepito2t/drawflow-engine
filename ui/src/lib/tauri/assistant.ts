import { Channel, invoke } from "@tauri-apps/api/core";
import type { ConversationMessage } from "../assistant-chat";
import { engineMessageSchema, type EngineMessage } from "../engine-message";
import { engineRequest } from "./engine";

export function startAssistantChat(
  messages: ConversationMessage[],
  onMessage: (message: EngineMessage) => void,
): Promise<void> {
  const channel = new Channel<unknown>((raw) => {
    onMessage(engineMessageSchema.parse(raw));
  });
  return invoke<undefined>("assistant_chat", { conversation: { messages }, onEvent: channel });
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
  onMessage: (message: EngineMessage) => void,
): Promise<string> {
  const channel = new Channel<unknown>((raw) => {
    onMessage(engineMessageSchema.parse(raw));
  });
  return invoke<string>("pull_model", { model, onEvent: channel });
}

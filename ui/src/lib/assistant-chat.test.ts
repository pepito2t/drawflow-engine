import { describe, expect, it } from "vitest";
import type { AssistantEvent } from "./assistant-events";
import { parseAssistantLine } from "./assistant-events";
import {
  chatReducer,
  conversationWith,
  INITIAL_CHAT,
  streamingAnswer,
  toolLabel,
  type AssistantEntry,
  type ChatAction,
  type ChatState,
} from "./assistant-chat";

const FIRST_ANSWER_ID = 2;
const event = (payload: AssistantEvent, answerId = FIRST_ANSWER_ID): ChatAction => ({
  type: "event",
  answerId,
  event: payload,
});

function reduce(actions: ChatAction[], state: ChatState = INITIAL_CHAT): ChatState {
  return actions.reduce(chatReducer, state);
}

function lastAnswer(state: ChatState): AssistantEntry {
  const last = state.entries.at(-1);
  if (last?.role !== "assistant") {
    throw new Error("no answer");
  }
  return last;
}

describe("chatReducer", () => {
  it("streams text into the answer then completes it", () => {
    const state = reduce([
      { type: "sent", text: "Bonjour" },
      event({ type: "delta", text: "Bon" }),
      event({ type: "delta", text: "jour !" }),
      event({ type: "done" }),
    ]);

    expect(state.entries.map((entry) => entry.role)).toEqual(["user", "assistant"]);
    expect(lastAnswer(state)).toMatchObject({ text: "Bonjour !", status: "done", error: null });
    expect(streamingAnswer(state)).toBeNull();
  });

  it("tracks tool calls and their results", () => {
    const state = reduce([
      { type: "sent", text: "Fonctionnalités ?" },
      event({ type: "tool_call", id: "a", name: "list_features", arguments: {} }),
      event({ type: "tool_call", id: "b", name: "list_presets", arguments: {} }),
      event({ type: "tool_result", id: "a", name: "list_features", ok: true }),
    ]);

    expect(lastAnswer(state).tools).toEqual([
      { id: "a", name: "list_features", status: "succeeded" },
      { id: "b", name: "list_presets", status: "running" },
    ]);
  });

  it("keeps the engine error with its hint", () => {
    const state = reduce([
      { type: "sent", text: "Salut" },
      event({
        type: "error",
        message: "Le modèle local ne répond pas.",
        hint: "Lancez Ollama.",
        file: null,
      }),
      { type: "exited", answerId: FIRST_ANSWER_ID, code: 1 },
    ]);

    expect(lastAnswer(state)).toMatchObject({
      status: "failed",
      error: { message: "Le modèle local ne répond pas.", hint: "Lancez Ollama." },
    });
  });

  it("reports a silent crash of the engine", () => {
    const state = reduce([
      { type: "sent", text: "Salut" },
      { type: "exited", answerId: FIRST_ANSWER_ID, code: 2 },
    ]);

    expect(lastAnswer(state).status).toBe("failed");
    expect(lastAnswer(state).error?.message).toContain("sans terminer");
  });

  it("ignores late messages of a stopped answer once the next question is asked", () => {
    const state = reduce([
      { type: "sent", text: "Première" },
      event({ type: "tool_call", id: "a", name: "list_features", arguments: {} }),
      { type: "cancelled" },
      { type: "sent", text: "Deuxième" },
      event({ type: "delta", text: "trop tard" }),
      { type: "exited", answerId: FIRST_ANSWER_ID, code: null },
    ]);

    const first = state.entries[1];
    expect(first).toMatchObject({ status: "cancelled", tools: [{ status: "failed" }] });
    expect(lastAnswer(state)).toMatchObject({ text: "", status: "streaming" });
  });

  it("adds a pending proposal that stays actionable after the answer ends", () => {
    const proposal = event({
      type: "proposal",
      id: "call-1",
      kind: "feature",
      feature: "soumission",
      feature_name: "Soumission",
      label: "Soumission",
      preset_id: null,
      inputs: { output_folder: "C:\\Sortie" },
    });
    const shown = reduce([{ type: "sent", text: "Lance" }, proposal, event({ type: "done" })]);
    expect(lastAnswer(shown).proposals).toMatchObject([{ id: "call-1", status: "pending" }]);

    const launched = chatReducer(shown, {
      type: "proposal",
      proposalId: "call-1",
      status: "launched",
    });
    expect(lastAnswer(launched).proposals[0]?.status).toBe("launched");

    const failed = chatReducer(shown, {
      type: "proposal",
      proposalId: "call-1",
      status: "failed",
      error: "Déjà en cours",
    });
    expect(lastAnswer(failed).proposals[0]).toMatchObject({
      status: "failed",
      error: "Déjà en cours",
    });
  });

  it("clears the conversation", () => {
    const state = reduce([{ type: "sent", text: "Salut" }, { type: "cleared" }]);

    expect(state.entries).toEqual([]);
  });
});

describe("conversationWith", () => {
  it("sends the visible history without empty answers, then the new question", () => {
    const state = reduce([
      { type: "sent", text: "Salut" },
      event({ type: "delta", text: "\n\nBonjour" }),
      event({ type: "done" }),
      { type: "sent", text: "Encore" },
      { type: "cancelled" },
    ]);

    expect(conversationWith(state, "Merci")).toEqual([
      { role: "user", content: "Salut" },
      { role: "assistant", content: "Bonjour" },
      { role: "user", content: "Encore" },
      { role: "user", content: "Merci" },
    ]);
  });
});

describe("assistant events", () => {
  it("turns an unreadable line into an error event", () => {
    expect(parseAssistantLine("pas du json")).toMatchObject({ type: "error" });
    expect(parseAssistantLine('{"type":"delta","text":"é"}')).toEqual({ type: "delta", text: "é" });
  });

  it("labels known tools in French", () => {
    expect(toolLabel("list_features")).toBe("Consulte les fonctionnalités");
    expect(toolLabel("other")).toBe("Outil other");
  });
});

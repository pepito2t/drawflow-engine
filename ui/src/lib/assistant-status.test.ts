import { describe, expect, it } from "vitest";
import { parseAssistantStatus, selectableModels } from "./assistant-status";

const status = (model: string, available: string[]) => ({
  server_url: "http://127.0.0.1:1234/v1",
  model,
  available,
  installed: available.includes(model),
});

describe("selectableModels", () => {
  it("lists the chat models without the embedding ones", () => {
    expect(
      selectableModels(
        status("qwen/qwen3.5-9b", ["qwen/qwen3.5-9b", "nomic-embed-text", "llama3"]),
      ),
    ).toEqual(["qwen/qwen3.5-9b", "llama3"]);
  });

  it("keeps a configured model that is not installed so the select shows it", () => {
    expect(selectableModels(status("qwen2.5:7b", ["llama3"]))).toEqual(["qwen2.5:7b", "llama3"]);
  });
});

describe("parseAssistantStatus", () => {
  it("rejects an unexpected answer", () => {
    expect(() => parseAssistantStatus('{"model": 1}')).toThrow();
  });
});

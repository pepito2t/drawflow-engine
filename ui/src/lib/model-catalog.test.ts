import { describe, expect, it } from "vitest";
import { fitsInMemory, parseModelCatalog, visibleModels, type ModelCatalog } from "./model-catalog";

const CATALOG: ModelCatalog = parseModelCatalog(
  JSON.stringify({
    memory_gb: 17.2,
    recommended: "qwen3.5:9b",
    configured: "qwen3.5:4b",
    server_url: "http://127.0.0.1:11434/v1",
    is_ollama: true,
    models: [
      {
        name: "qwen3.5:27b",
        label: "Qwen 3.5 · 27B",
        size_gb: 17,
        min_memory_gb: 32,
        description: "Le plus capable",
        installed: false,
      },
      {
        name: "qwen3.5:9b",
        label: "Qwen 3.5 · 9B",
        size_gb: 6.6,
        min_memory_gb: 16,
        description: "Équilibre",
        installed: false,
      },
      {
        name: "qwen3.5:4b",
        label: "Qwen 3.5 · 4B",
        size_gb: 3.4,
        min_memory_gb: 8,
        description: "Léger",
        installed: true,
      },
      {
        name: "mistral-nemo:latest",
        label: "mistral-nemo:latest",
        size_gb: 7.1,
        min_memory_gb: null,
        description: "",
        installed: true,
      },
    ],
  }),
);

describe("visibleModels", () => {
  it("shows the recommendation first, then installed models", () => {
    expect(visibleModels(CATALOG, "").map((model) => model.name)).toEqual([
      "qwen3.5:9b",
      "qwen3.5:4b",
      "mistral-nemo:latest",
      "qwen3.5:27b",
    ]);
  });

  it("searches names and descriptions, ignoring case and accents", () => {
    expect(visibleModels(CATALOG, "EQUILIBRE").map((model) => model.name)).toEqual(["qwen3.5:9b"]);
    expect(visibleModels(CATALOG, "nemo").map((model) => model.name)).toEqual([
      "mistral-nemo:latest",
    ]);
  });
});

describe("fitsInMemory", () => {
  it("flags models that need more memory than the computer has", () => {
    const [big, balanced] = CATALOG.models;

    expect(big && fitsInMemory(CATALOG, big)).toBe(false);
    expect(balanced && fitsInMemory(CATALOG, balanced)).toBe(true);
  });
});

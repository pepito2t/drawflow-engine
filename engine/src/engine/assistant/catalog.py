"""Local models known to call Drawflow's tools well, and which one suits this computer."""

from dataclasses import dataclass

from engine.assistant.messages import t

BYTES_PER_GB = 1_000_000_000


@dataclass(frozen=True)
class CatalogModel:
    name: str
    label: str
    size_gb: float
    min_memory_gb: int
    description: str


# Most capable first: the recommendation is the first one that fits in memory.
CATALOG = (
    CatalogModel("qwen3.5:27b", "Qwen 3.5 · 27B", 17.0, 32, t("catalog.qwen35_27b")),
    CatalogModel("qwen3.5:9b", "Qwen 3.5 · 9B", 6.6, 16, t("catalog.qwen35_9b")),
    CatalogModel("qwen3:8b", "Qwen 3 · 8B", 5.2, 16, t("catalog.qwen3_8b")),
    CatalogModel("llama3.1:8b", "Llama 3.1 · 8B", 4.9, 16, t("catalog.llama31_8b")),
    CatalogModel("qwen3.5:4b", "Qwen 3.5 · 4B", 3.4, 8, t("catalog.qwen35_4b")),
    CatalogModel("qwen3.5:2b", "Qwen 3.5 · 2B", 2.7, 4, t("catalog.qwen35_2b")),
)
RECOMMENDABLE = ("qwen3.5:27b", "qwen3.5:9b", "qwen3.5:4b", "qwen3.5:2b")
FALLBACK_RECOMMENDATION = "qwen3.5:9b"


def recommend(memory_bytes: int | None) -> str:
    if memory_bytes is None:
        return FALLBACK_RECOMMENDATION
    memory_gb = memory_bytes / BYTES_PER_GB
    for model in CATALOG:
        if model.name in RECOMMENDABLE and model.min_memory_gb <= memory_gb:
            return model.name
    return RECOMMENDABLE[-1]

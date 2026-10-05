"""Local models known to call Drawflow's tools well, and which one suits this computer."""

from dataclasses import dataclass

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
    CatalogModel(
        "qwen3.5:27b", "Qwen 3.5 · 27B", 17.0, 32, "Le plus capable, pour les postes très équipés."
    ),
    CatalogModel(
        "qwen3.5:9b", "Qwen 3.5 · 9B", 6.6, 16, "Le meilleur équilibre pour un poste récent."
    ),
    CatalogModel("qwen3:8b", "Qwen 3 · 8B", 5.2, 16, "Génération précédente, très éprouvée."),
    CatalogModel(
        "llama3.1:8b", "Llama 3.1 · 8B", 4.9, 16, "Alternative de Meta, moins bonne en français."
    ),
    CatalogModel("qwen3.5:4b", "Qwen 3.5 · 4B", 3.4, 8, "Pour les postes avec peu de mémoire."),
    CatalogModel("qwen3.5:2b", "Qwen 3.5 · 2B", 2.7, 4, "Très léger, réponses plus simples."),
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

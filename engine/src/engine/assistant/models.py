"""`engine assistant catalog|pull|model-delete`: choose, download and remove local models."""

import re
from pathlib import Path
from typing import Any

import anyio
import httpx

from engine.assistant.catalog import BYTES_PER_GB, CATALOG, recommend
from engine.assistant.errors import AssistantError
from engine.core.errors import InvalidInputError
from engine.core.events import Emit, ProgressEvent, ResultEvent
from engine.core.settings import load_assistant_settings
from engine.setup.machine import LocalMachine, Machine
from engine.setup.ollama import delete_model, installed_sizes, is_ollama, pull_model

# Ollama names: "family[:tag]", optionally prefixed by a namespace ("user/model").
MODEL_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*(/[a-z0-9][a-z0-9._-]*)?(:[a-z0-9][a-z0-9._-]*)?$")
PERCENT = 100
NOT_OLLAMA_HINT = (
    "Le téléchargement passe par Ollama. Avec LM Studio, téléchargez le modèle depuis "
    "LM Studio puis choisissez-le dans le panneau de l'assistant."
)


def catalog(
    settings: Path,
    machine: Machine | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    memory = (machine or LocalMachine()).memory_bytes
    assistant = load_assistant_settings(settings)
    server = anyio.run(_server_state, assistant.model_server_url, transport)
    installed: dict[str, int] = server["installed"]
    listed = [
        {
            "name": model.name,
            "label": model.label,
            "size_gb": model.size_gb,
            "min_memory_gb": model.min_memory_gb,
            "description": model.description,
            "installed": model.name in installed,
        }
        for model in CATALOG
    ]
    known = {model.name for model in CATALOG}
    listed += [
        {
            "name": name,
            "label": name,
            "size_gb": round(size / BYTES_PER_GB, 1),
            "min_memory_gb": None,
            "description": "",
            "installed": True,
        }
        for name, size in sorted(installed.items())
        if name not in known
    ]
    return {
        "memory_gb": None if memory is None else round(memory / BYTES_PER_GB, 1),
        "recommended": recommend(memory),
        "configured": assistant.model,
        "server_url": assistant.model_server_url,
        "is_ollama": server["is_ollama"],
        "models": listed,
    }


def pull(
    settings: Path, model: str, emit: Emit, transport: httpx.AsyncBaseTransport | None = None
) -> None:
    name = _valid_name(model)
    url = load_assistant_settings(settings).model_server_url

    def on_percent(percent: int, status: str) -> None:
        emit(ProgressEvent(current=percent, total=PERCENT, message=status))

    async def download() -> None:
        if not await is_ollama(url, transport):
            raise AssistantError("Ollama ne répond pas.", hint=NOT_OLLAMA_HINT)
        await pull_model(url, name, on_percent, transport)

    anyio.run(download)
    emit(ResultEvent(summary=f"Modèle {name} téléchargé."))


def remove(
    settings: Path, raw: dict[str, Any], transport: httpx.AsyncBaseTransport | None = None
) -> dict[str, Any]:
    name = _valid_name(str(raw.get("model", "")))
    url = load_assistant_settings(settings).model_server_url
    anyio.run(delete_model, url, name, transport)
    return {"deleted": name}


async def _server_state(url: str, transport: httpx.AsyncBaseTransport | None) -> dict[str, Any]:
    if not await is_ollama(url, transport):
        return {"is_ollama": False, "installed": {}}
    return {"is_ollama": True, "installed": await installed_sizes(url, transport)}


def _valid_name(model: str) -> str:
    name = model.strip().lower()
    if not MODEL_NAME.fullmatch(name):
        raise InvalidInputError(
            f"« {model} » n'est pas un nom de modèle valide.",
            hint="Exemple : qwen3.5:9b (voir ollama.com/library).",
        )
    return name

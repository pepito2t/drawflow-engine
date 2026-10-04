"""Ollama's own API: download a model with progress, wait for the server to come up."""

import json
from collections.abc import Callable

import anyio
import httpx

from engine.assistant.errors import AssistantError

OPENAI_PATH_SUFFIX = "/v1"
PULL_PATH = "/api/pull"
VERSION_PATH = "/api/version"
# A model is several gigabytes: only the gap between two chunks is bounded.
PULL_TIMEOUT = httpx.Timeout(connect=5.0, read=300.0, write=30.0, pool=5.0)
PROBE_TIMEOUT = httpx.Timeout(3.0)
START_WAIT_SECONDS = 30.0
START_POLL_SECONDS = 1.0
PERCENT = 100

OnPercent = Callable[[int, str], None]


def api_root(base_url: str) -> str:
    return base_url.removesuffix(OPENAI_PATH_SUFFIX)


async def is_ollama(base_url: str, transport: httpx.AsyncBaseTransport | None = None) -> bool:
    async with httpx.AsyncClient(timeout=PROBE_TIMEOUT, transport=transport) as http:
        try:
            response = await http.get(api_root(base_url) + VERSION_PATH)
        except httpx.TransportError:
            return False
    # Other servers (LM Studio) answer unknown routes with 200 and an error body.
    try:
        payload = response.json()
    except ValueError:
        return False
    return response.is_success and isinstance(payload, dict) and "version" in payload


async def wait_until_up(
    base_url: str,
    transport: httpx.AsyncBaseTransport | None = None,
    wait_seconds: float = START_WAIT_SECONDS,
) -> bool:
    with anyio.move_on_after(wait_seconds):
        while not await is_ollama(base_url, transport):
            await anyio.sleep(START_POLL_SECONDS)
        return True
    return False


async def pull_model(
    base_url: str,
    model: str,
    on_percent: OnPercent,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    body = {"model": model, "stream": True}
    async with (
        httpx.AsyncClient(timeout=PULL_TIMEOUT, transport=transport) as http,
        http.stream("POST", api_root(base_url) + PULL_PATH, json=body) as response,
    ):
        if not response.is_success:
            raise AssistantError(
                f"Ollama a refusé le téléchargement de « {model} » (HTTP {response.status_code}).",
                hint="Vérifiez le nom du modèle sur ollama.com/library.",
            )
        async for line in response.aiter_lines():
            if line.strip():
                _report(json.loads(line), model, on_percent)


def _report(update: dict[str, object], model: str, on_percent: OnPercent) -> None:
    if "error" in update:
        raise AssistantError(
            f"Téléchargement de « {model} » impossible : {update['error']}",
            hint="Vérifiez la connexion Internet et l'espace disque, puis réessayez.",
        )
    total, completed = update.get("total"), update.get("completed")
    status = str(update.get("status", ""))
    if isinstance(total, int) and isinstance(completed, int) and total > 0:
        on_percent(completed * PERCENT // total, status)

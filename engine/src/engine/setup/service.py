"""Entry point of `engine setup scan`."""

from pathlib import Path
from typing import Any

import anyio
import httpx

from engine.assistant.catalog import recommend
from engine.assistant.errors import AssistantError
from engine.assistant.model_client import ModelClient
from engine.core.registry import discover_modules
from engine.core.settings import (
    ASSISTANT_SECTION_ID,
    load_assistant_settings,
    load_general_settings,
    read_document,
    save_settings,
)
from engine.core.settings_models import AssistantSettings
from engine.setup.machine import LocalMachine, Machine
from engine.setup.ollama import is_ollama
from engine.setup.scan import ModelServerState, build_report
from engine.setup.stream_dock import AUTOCAD_PLUGIN_LATEST_URL, latest_release_version

# The scan must answer quickly: a local server that is up replies in milliseconds.
SCAN_TIMEOUT = httpx.Timeout(3.0)


def scan(
    settings: Path,
    machine: Machine | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
    app_version: str | None = None,
) -> dict[str, Any]:
    general = load_general_settings(settings)
    assistant = _with_default_model(settings, machine or LocalMachine())
    server = anyio.run(_probe_server, assistant.model_server_url, transport)
    autocad_latest = anyio.run(latest_release_version, AUTOCAD_PLUGIN_LATEST_URL, transport)
    report = build_report(
        machine or LocalMachine(),
        general.oda_converter_path,
        assistant,
        server,
        app_version,
        autocad_latest,
    )
    return report.model_dump(mode="json")


def _with_default_model(settings: Path, machine: Machine) -> AssistantSettings:
    """Until the user picks a model, the one that fits this computer's memory is stored."""
    assistant = load_assistant_settings(settings)
    chosen = read_document(settings).get(ASSISTANT_SECTION_ID, {}).get("model")
    if chosen:
        return assistant
    recommended = recommend(machine.memory_bytes)
    section = {**assistant.model_dump(mode="json"), "model": recommended}
    save_settings(settings, {ASSISTANT_SECTION_ID: section}, discover_modules())
    return assistant.model_copy(update={"model": recommended})


async def _probe_server(
    base_url: str, transport: httpx.AsyncBaseTransport | None
) -> ModelServerState:
    client = ModelClient(base_url, model="", transport=transport, timeout=SCAN_TIMEOUT)
    try:
        available = await client.list_models()
    except AssistantError:
        return ModelServerState(reachable=False, is_ollama=False, available=[])
    return ModelServerState(
        reachable=True, is_ollama=await is_ollama(base_url, transport), available=available
    )

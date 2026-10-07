"""Entry point of `engine setup scan`."""

from pathlib import Path
from typing import Any

import anyio
import httpx

from engine.assistant.errors import AssistantError
from engine.assistant.model_client import ModelClient
from engine.core.settings import load_general_settings
from engine.setup.machine import LocalMachine, Machine
from engine.setup.model_choice import effective_assistant_settings
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
    """Read-only: the scan reports the recommended model, it never writes the settings."""
    this_machine = machine or LocalMachine()
    general = load_general_settings(settings)
    assistant = effective_assistant_settings(settings, this_machine)
    server = anyio.run(_probe_server, assistant.model_server_url, transport)
    autocad_latest = anyio.run(latest_release_version, AUTOCAD_PLUGIN_LATEST_URL, transport)
    report = build_report(
        this_machine, general.oda_converter_path, assistant, server, app_version, autocad_latest
    )
    return report.model_dump(mode="json")


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

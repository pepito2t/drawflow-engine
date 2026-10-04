"""Entry point of `engine setup scan`."""

from pathlib import Path
from typing import Any

import anyio
import httpx

from engine.assistant.errors import AssistantError
from engine.assistant.model_client import ModelClient
from engine.core.settings import load_assistant_settings, load_general_settings
from engine.setup.machine import LocalMachine, Machine
from engine.setup.ollama import is_ollama
from engine.setup.scan import ModelServerState, build_report

# The scan must answer quickly: a local server that is up replies in milliseconds.
SCAN_TIMEOUT = httpx.Timeout(3.0)


def scan(
    settings: Path,
    machine: Machine | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    general = load_general_settings(settings)
    assistant = load_assistant_settings(settings)
    server = anyio.run(_probe_server, assistant.model_server_url, transport)
    report = build_report(machine or LocalMachine(), general.oda_converter_path, assistant, server)
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

"""Entry points of the `engine assistant` commands."""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import anyio
import httpx
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from pydantic import ValidationError

from engine.assistant.agent import run_turn
from engine.assistant.conversation import ChatRequest
from engine.assistant.events import EmitAssistant
from engine.assistant.mcp_server import server_parameters
from engine.assistant.model_client import ModelClient
from engine.assistant.toolbox import McpToolBox
from engine.core.errors import EngineError, InvalidInputError
from engine.core.settings import load_assistant_settings


def chat(
    settings: Path,
    raw_request: dict[str, Any],
    emit: EmitAssistant,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    request = _parse_request(raw_request)
    model = _model_client(settings, transport)

    async def turn() -> None:
        async with (
            stdio_client(server_parameters(settings)) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            await run_turn(request, model, McpToolBox(session), emit)

    _run(turn)


def list_models(
    settings: Path, transport: httpx.AsyncBaseTransport | None = None
) -> dict[str, Any]:
    model = _model_client(settings, transport)
    available: list[str] = []

    async def query() -> None:
        available.extend(await model.list_models())

    _run(query)
    return {
        "server_url": model.base_url,
        "model": model.model,
        "available": available,
        "installed": model.model in available,
    }


def _model_client(settings: Path, transport: httpx.AsyncBaseTransport | None) -> ModelClient:
    assistant = load_assistant_settings(settings)
    return ModelClient(assistant.model_server_url, assistant.model, transport)


def _parse_request(raw: dict[str, Any]) -> ChatRequest:
    try:
        return ChatRequest.model_validate(raw)
    except ValidationError as error:
        raise InvalidInputError("Conversation invalide.", hint=str(error)) from error


def _run(task: Callable[[], Awaitable[None]]) -> None:
    try:
        anyio.run(task)
    except BaseExceptionGroup as group:
        # The MCP transport runs in a task group, which wraps the business error we raised.
        raise _first_engine_error(group) or group from None


def _first_engine_error(group: BaseExceptionGroup) -> EngineError | None:
    for error in group.exceptions:
        if isinstance(error, EngineError):
            return error
        if isinstance(error, BaseExceptionGroup):
            nested = _first_engine_error(group=error)
            if nested is not None:
                return nested
    return None

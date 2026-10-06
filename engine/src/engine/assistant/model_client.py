"""Streaming client for a local model served through an OpenAI-compatible API."""

import json
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from engine.assistant.errors import SETTINGS_HINT, AssistantError, ModelUnavailableError
from engine.assistant.messages import t

STREAM_PREFIX = "data:"
STREAM_END = "[DONE]"
# A local model can take a minute to load into memory before the first token.
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=180.0, write=30.0, pool=5.0)
HTTP_NOT_FOUND = 404

JsonObject = dict[str, Any]
OnText = Callable[[str], None]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ModelReply:
    text: str
    tool_calls: list[ToolCall]


@dataclass
class _PendingCall:
    id: str = ""
    name: str = ""
    arguments: list[str] = field(default_factory=list)


# Reasoning models (Qwen 3.x…) think for tens of seconds before the first word; the assistant
# answers short, tool-grounded questions and does better without it.
REASONING_EFFORT = "none"


MEMORY_MARKERS = ("memory", "mémoire")
SERVER_ERROR_MAX_LENGTH = 300


def _server_error(response: httpx.Response) -> str:
    """Ollama answers {"error": {"message": …}} or {"error": "…"}; others plain text."""
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()[:SERVER_ERROR_MAX_LENGTH]
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        error = error.get("message")
    return str(error).strip()[:SERVER_ERROR_MAX_LENGTH] if error else ""


class ModelClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: httpx.Timeout = REQUEST_TIMEOUT,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._transport = transport
        self._timeout = timeout

    async def list_models(self) -> list[str]:
        async with self._http() as http:
            response = await self._send(http, http.build_request("GET", "/models"))
            await response.aread()
        try:
            return sorted(str(entry["id"]) for entry in response.json()["data"])
        except (ValueError, KeyError, TypeError) as error:
            raise AssistantError(t("model_client.unreadable_server_reply")) from error

    async def complete(
        self, messages: list[JsonObject], tools: list[JsonObject], on_text: OnText
    ) -> ModelReply:
        body: JsonObject = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "reasoning_effort": REASONING_EFFORT,
        }
        if tools:
            body["tools"] = tools
        async with self._http() as http:
            request = http.build_request("POST", "/chat/completions", json=body)
            response = await self._send(http, request)
            try:
                return await _read_stream(response.aiter_lines(), on_text)
            except httpx.TransportError as error:
                raise self._unreachable() from error
            finally:
                await response.aclose()

    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url, timeout=self._timeout, transport=self._transport
        )

    async def _send(self, http: httpx.AsyncClient, request: httpx.Request) -> httpx.Response:
        try:
            response = await http.send(request, stream=True)
        except httpx.TransportError as error:
            raise self._unreachable() from error
        if response.is_success:
            return response
        await response.aread()
        detail = _server_error(response)
        await response.aclose()
        if response.status_code == HTTP_NOT_FOUND:
            raise ModelUnavailableError(
                t("model_client.model_not_found", model=self.model),
                hint=t(
                    "model_client.model_not_found.hint",
                    model=self.model,
                    settings_hint=SETTINGS_HINT,
                ),
            )
        if any(marker in detail.lower() for marker in MEMORY_MARKERS):
            raise AssistantError(
                t("model_client.out_of_memory", model=self.model),
                hint=t("model_client.out_of_memory.hint"),
            )
        status = response.status_code
        if detail:
            message = t("model_client.refused_with_detail", status=status, detail=detail)
        else:
            message = t("model_client.refused", status=status)
        raise AssistantError(message, hint=SETTINGS_HINT)

    def _unreachable(self) -> ModelUnavailableError:
        return ModelUnavailableError(
            t("model_client.unreachable", url=self.base_url),
            hint=t("model_client.unreachable.hint", settings_hint=SETTINGS_HINT),
        )


async def _read_stream(lines: AsyncIterator[str], on_text: OnText) -> ModelReply:
    text: list[str] = []
    pending: dict[int, _PendingCall] = {}
    async for line in lines:
        stripped = line.strip()
        if not stripped.startswith(STREAM_PREFIX):
            continue
        payload = stripped.removeprefix(STREAM_PREFIX).strip()
        if payload == STREAM_END:
            break
        if not payload:
            continue
        for delta in _deltas(payload):
            content = delta.get("content")
            if isinstance(content, str) and content:
                text.append(content)
                on_text(content)
            for raw_call in delta.get("tool_calls") or []:
                _merge_tool_call(pending, raw_call)
    calls = [ToolCall(call.id, call.name, "".join(call.arguments)) for call in pending.values()]
    return ModelReply(text="".join(text), tool_calls=calls)


def _deltas(payload: str) -> list[JsonObject]:
    try:
        chunk = json.loads(payload)
        return [choice["delta"] for choice in chunk["choices"] if choice.get("delta")]
    except (ValueError, KeyError, TypeError) as error:
        raise AssistantError(t("model_client.unreadable_model_reply")) from error


def _merge_tool_call(pending: dict[int, _PendingCall], raw_call: JsonObject) -> None:
    """Tool calls arrive in fragments keyed by index: name first, arguments in pieces."""
    call = pending.setdefault(int(raw_call.get("index", len(pending))), _PendingCall())
    call.id = raw_call.get("id") or call.id or f"call-{len(pending)}"
    function = raw_call.get("function") or {}
    call.name = function.get("name") or call.name
    if function.get("arguments"):
        call.arguments.append(str(function["arguments"]))

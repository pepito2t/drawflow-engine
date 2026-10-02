"""OpenAI-compatible model double served through an httpx transport (no network)."""

import json
from collections.abc import Iterator
from typing import Any

import httpx

JsonObject = dict[str, Any]


def text_reply(*pieces: str) -> list[JsonObject]:
    return [{"content": piece} for piece in pieces]


def tool_reply(name: str, arguments: str = "{}", call_id: str = "call-1") -> list[JsonObject]:
    """Splits the call like real servers do: name first, then the arguments in fragments."""
    middle = len(arguments) // 2
    return [
        {"tool_calls": [{"index": 0, "id": call_id, "function": {"name": name}}]},
        {"tool_calls": [{"index": 0, "function": {"arguments": arguments[:middle]}}]},
        {"tool_calls": [{"index": 0, "function": {"arguments": arguments[middle:]}}]},
    ]


class FakeModelServer:
    def __init__(self, *replies: list[JsonObject], models: tuple[str, ...] = ()) -> None:
        self._replies: Iterator[list[JsonObject]] = iter(replies)
        self.models = models
        self.requests: list[JsonObject] = []

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": name} for name in self.models]})
        self.requests.append(json.loads(request.content))
        return httpx.Response(200, content=_sse(next(self._replies)))


def _sse(deltas: list[JsonObject]) -> bytes:
    lines = [f"data: {json.dumps({'choices': [{'delta': delta}]})}" for delta in deltas]
    return ("\n\n".join([*lines, "data: [DONE]"]) + "\n\n").encode()

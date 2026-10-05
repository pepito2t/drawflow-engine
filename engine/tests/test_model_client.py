import anyio
import httpx
import pytest

from engine.assistant.errors import AssistantError, ModelUnavailableError
from engine.assistant.model_client import ModelClient, ModelReply
from engine.testing.fake_model import FakeModelServer, text_reply, tool_reply

BASE_URL = "http://127.0.0.1:11434/v1"


def complete(transport: httpx.AsyncBaseTransport, received: list[str]) -> ModelReply:
    client = ModelClient(BASE_URL, "qwen2.5:7b", transport)

    async def call() -> ModelReply:
        return await client.complete([{"role": "user", "content": "Salut"}], [], received.append)

    return anyio.run(call)


def test_streamed_text_is_forwarded_piece_by_piece() -> None:
    received: list[str] = []
    server = FakeModelServer(text_reply("Bon", "jour é"))

    reply = complete(server.transport(), received)

    assert received == ["Bon", "jour é"]
    assert reply == ModelReply(text="Bonjour é", tool_calls=[])
    assert server.requests[0]["model"] == "qwen2.5:7b"
    assert server.requests[0]["reasoning_effort"] == "none"
    assert "tools" not in server.requests[0]


def test_fragmented_tool_call_is_reassembled() -> None:
    server = FakeModelServer(tool_reply("list_presets", '{"feature": "dwg-parts"}'))

    reply = complete(server.transport(), [])

    [call] = reply.tool_calls
    assert (call.id, call.name, call.arguments) == (
        "call-1",
        "list_presets",
        '{"feature": "dwg-parts"}',
    )


def test_unreachable_server_explains_how_to_start_the_model() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(ModelUnavailableError, match="ne répond pas") as caught:
        complete(httpx.MockTransport(refuse), [])
    assert caught.value.hint is not None
    assert "Ollama" in caught.value.hint


def test_missing_model_suggests_installing_it() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(404, json={"error": "not found"}))

    with pytest.raises(ModelUnavailableError, match="introuvable") as caught:
        complete(transport, [])
    assert caught.value.hint is not None
    assert "ollama pull qwen2.5:7b" in caught.value.hint


def test_server_error_is_reported_with_its_status() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(500))

    with pytest.raises(AssistantError, match="HTTP 500"):
        complete(transport, [])


def test_unreadable_chunk_is_a_readable_error() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=b"data: {oops\n\n"))

    with pytest.raises(AssistantError, match="illisible"):
        complete(transport, [])


def test_models_are_listed_sorted() -> None:
    server = FakeModelServer(models=("qwen2.5:7b", "llama3.1:8b"))
    client = ModelClient(BASE_URL, "qwen2.5:7b", server.transport())

    assert anyio.run(client.list_models) == ["llama3.1:8b", "qwen2.5:7b"]

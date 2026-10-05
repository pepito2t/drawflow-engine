import json
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import anyio
import httpx
import pytest

from engine.assistant import service
from engine.assistant.agent import MAX_TOOL_ROUNDS, run_turn
from engine.assistant.conversation import ChatRequest
from engine.assistant.errors import AssistantError, ModelUnavailableError
from engine.assistant.events import AssistantEvent, Proposal
from engine.assistant.model_client import ModelClient
from engine.assistant.toolbox import ToolOutcome
from engine.cli import EXIT_BUSINESS_ERROR
from engine.core.errors import InvalidInputError
from engine.testing.fake_model import FakeModelServer, text_reply, tool_reply

BASE_URL = "http://127.0.0.1:11434/v1"
QUESTION = {"messages": [{"role": "user", "content": "Quelles fonctionnalités as-tu ?"}]}


class RecordingToolBox:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def definitions(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": "list_presets", "parameters": {}}}]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        self.calls.append((name, arguments))
        return ToolOutcome(ok=True, text='{"presets": []}')


def turn(server: FakeModelServer, tools: RecordingToolBox) -> list[AssistantEvent]:
    events: list[AssistantEvent] = []
    model = ModelClient(BASE_URL, "qwen2.5:7b", server.transport())
    request = ChatRequest.model_validate(QUESTION)
    anyio.run(run_turn, request, model, tools, events.append)
    return events


def kinds(events: list[AssistantEvent]) -> list[str]:
    return [event.type for event in events]


def test_answer_without_tools_streams_then_ends() -> None:
    events = turn(FakeModelServer(text_reply("Bonjour")), RecordingToolBox())

    assert kinds(events) == ["delta", "done"]


def test_tool_call_is_executed_and_its_result_sent_back_to_the_model() -> None:
    server = FakeModelServer(tool_reply("list_presets", '{"feature": "x"}'), text_reply("Aucun"))
    tools = RecordingToolBox()

    events = turn(server, tools)

    assert kinds(events) == ["tool_call", "tool_result", "delta", "done"]
    assert tools.calls == [("list_presets", {"feature": "x"})]
    follow_up = server.requests[1]["messages"]
    assert follow_up[0]["role"] == "system"
    assert follow_up[-2]["tool_calls"][0]["function"]["name"] == "list_presets"
    assert follow_up[-1] == {"role": "tool", "tool_call_id": "call-1", "content": '{"presets": []}'}


class ProposingToolBox(RecordingToolBox):
    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        proposal = Proposal(
            kind="preset",
            feature="soumission",
            feature_name="Soumission",
            label="Chantier Nord",
            preset_id="ab12cd34",
            inputs={},
        )
        return ToolOutcome(ok=True, text='{"proposal": "…"}', proposal=proposal)


def test_proposal_is_shown_and_the_model_is_told_nothing_runs_yet() -> None:
    server = FakeModelServer(tool_reply("propose_preset"), text_reply("À confirmer."))

    events = turn(server, ProposingToolBox())

    assert kinds(events) == ["tool_call", "tool_result", "proposal", "delta", "done"]
    proposal = events[2]
    assert proposal.type == "proposal"
    assert (proposal.id, proposal.label) == ("call-1", "Chantier Nord")
    assert "Rien n'est lancé" in server.requests[1]["messages"][-1]["content"]


def test_invalid_arguments_are_returned_to_the_model_without_calling_the_tool() -> None:
    server = FakeModelServer(tool_reply("list_presets", "{pas json"), text_reply("Pardon"))
    tools = RecordingToolBox()

    events = turn(server, tools)

    assert tools.calls == []
    result = events[1]
    assert result.type == "tool_result"
    assert not result.ok
    assert "invalides" in server.requests[1]["messages"][-1]["content"]


def test_endless_tool_calls_stop_with_a_readable_error() -> None:
    server = FakeModelServer(*[tool_reply("list_presets")] * MAX_TOOL_ROUNDS)

    with pytest.raises(AssistantError, match="appels d'outils"):
        turn(server, RecordingToolBox())


def test_conversation_must_end_with_a_user_message(tmp_path: Path) -> None:
    raw = {"messages": [{"role": "assistant", "content": "Bonjour"}]}

    with pytest.raises(InvalidInputError):
        service.chat(tmp_path / "settings.json", raw, lambda _: None)


def test_chat_uses_the_real_drawflow_mcp_server(tmp_path: Path) -> None:
    settings = tmp_path / "Réglages é" / "settings.json"
    server = FakeModelServer(tool_reply("list_features"), text_reply("Trois fonctionnalités."))
    events: list[AssistantEvent] = []

    service.chat(settings, QUESTION, events.append, server.transport())

    assert kinds(events) == ["tool_call", "tool_result", "delta", "done"]
    tool_names = {tool["function"]["name"] for tool in server.requests[0]["tools"]}
    assert {"list_features", "propose_feature", "propose_preset"} <= tool_names
    features = json.loads(server.requests[1]["messages"][-1]["content"])
    assert features["features"][0]["id"] == "dwg-parts"


def test_model_error_inside_the_mcp_session_is_not_wrapped(tmp_path: Path) -> None:
    missing_model = httpx.MockTransport(lambda _: httpx.Response(404))

    with pytest.raises(ModelUnavailableError, match="introuvable"):
        service.chat(tmp_path / "settings.json", QUESTION, lambda _: None, missing_model)


def test_models_report_whether_the_configured_model_is_installed(tmp_path: Path) -> None:
    server = FakeModelServer(models=("llama3.1:8b",))

    models = service.list_models(tmp_path / "settings.json", server.transport())

    assert models == {
        "server_url": BASE_URL,
        "model": "qwen3.5:9b",
        "available": ["llama3.1:8b"],
        "installed": False,
    }


def test_cli_reports_an_unreachable_model_as_an_error_event(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    url = f"http://127.0.0.1:{_closed_port()}/v1"
    settings.write_text(json.dumps({"assistant": {"model_server_url": url}}), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "engine.cli", "assistant", "models", "--settings", str(settings)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == EXIT_BUSINESS_ERROR
    event = json.loads(completed.stdout.splitlines()[-1])
    assert event["type"] == "error"
    assert "ne répond pas" in event["message"]


def _closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
    return port

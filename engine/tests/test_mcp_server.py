import json
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import anyio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult, ErrorData, TextContent

from engine.assistant.mcp_server import server_parameters
from engine.assistant.toolbox import McpToolBox, ToolOutcome
from engine.assistant.tools import describe_today
from engine.core.presets import PresetStore
from engine.core.registry import get_module

MCP_REQUEST_TIMEOUT = timedelta(seconds=60)
EXPECTED_TOOLS = {
    "list_features",
    "list_help_topics",
    "read_today",
    "list_presets",
    "list_runs",
    "read_run",
    "list_templates",
    "propose_feature",
    "propose_preset",
    "read_help",
}


async def _call_tools(settings: Path, *names: str) -> tuple[set[str], list[CallToolResult]]:
    async with (
        stdio_client(server_parameters(settings)) as (read, write),
        ClientSession(read, write, read_timeout_seconds=MCP_REQUEST_TIMEOUT) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        results = [await session.call_tool(name, {}) for name in names]
    return {tool.name for tool in tools.tools}, results


def _payload(result: CallToolResult) -> Any:
    content = result.content[0]
    assert isinstance(content, TextContent)
    return json.loads(content.text)


def test_client_lists_read_only_tools_and_reads_features(tmp_path: Path) -> None:
    settings = tmp_path / "Réglages é" / "settings.json"

    names, results = anyio.run(_call_tools, settings, "list_features", "list_presets")

    assert names == EXPECTED_TOOLS
    features, presets = (_payload(result) for result in results)
    assert [feature["id"] for feature in features["features"]] == [
        "dwg-parts",
        "pdf-report",
        "soumission",
    ]
    assert "properties" in features["features"][0]["inputs_schema"]
    assert presets == {"presets": []}


def test_unreadable_store_becomes_readable_tool_error(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    (tmp_path / "presets.json").write_text("{pas du json", encoding="utf-8")

    _, [result] = anyio.run(_call_tools, settings, "list_presets")

    assert result.isError
    content = result.content[0]
    assert isinstance(content, TextContent)
    assert "préréglages est illisible" in content.text


class _SilentSession:
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        raise McpError(ErrorData(code=408, message="Timed out"))


def test_tool_that_never_answers_is_reported_to_the_model() -> None:
    toolbox = McpToolBox(cast(ClientSession, _SilentSession()))

    outcome = anyio.run(toolbox.call, "list_features", {})

    assert not outcome.ok
    assert "n'a pas répondu" in outcome.text


async def _toolbox_call(settings: Path, name: str, arguments: dict[str, Any]) -> ToolOutcome:
    async with (
        stdio_client(server_parameters(settings)) as (read, write),
        ClientSession(read, write, read_timeout_seconds=MCP_REQUEST_TIMEOUT) as session,
    ):
        await session.initialize()
        return await McpToolBox(session).call(name, arguments)


def test_feature_proposal_is_validated_and_nothing_runs(tmp_path: Path) -> None:
    output = tmp_path / "Sortie é"
    inputs = {"folders": [str(tmp_path / "Soumissions")], "output_folder": str(output)}
    arguments = {"feature_id": "soumission", "inputs": inputs}

    outcome = anyio.run(_toolbox_call, tmp_path / "settings.json", "propose_feature", arguments)

    assert outcome.ok
    assert outcome.proposal is not None
    assert (outcome.proposal.kind, outcome.proposal.feature) == ("feature", "soumission")
    assert outcome.proposal.inputs["output_folder"] == str(output)
    assert outcome.proposal.inputs["recursive"] is True
    assert not output.exists()


def test_invalid_feature_inputs_are_refused_without_proposal(tmp_path: Path) -> None:
    arguments = {"feature_id": "soumission", "inputs": {"project": "Sans sortie"}}

    outcome = anyio.run(_toolbox_call, tmp_path / "settings.json", "propose_feature", arguments)

    assert not outcome.ok
    assert outcome.proposal is None
    assert "Entrées invalides" in outcome.text


def test_preset_proposal_carries_the_preset(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    preset = PresetStore(settings).save(
        get_module("soumission"),
        "Chantier Nord",
        {"folders": [str(tmp_path)], "output_folder": str(tmp_path)},
    )

    outcome = anyio.run(_toolbox_call, settings, "propose_preset", {"preset_id": preset.id})

    assert outcome.proposal is not None
    assert (outcome.proposal.kind, outcome.proposal.label) == ("preset", "Chantier Nord")
    assert outcome.proposal.preset_id == preset.id


def test_assistant_reads_the_guide_through_mcp(tmp_path: Path) -> None:
    outcome = anyio.run(
        _toolbox_call, tmp_path / "settings.json", "read_help", {"topic": "stream dock"}
    )

    assert outcome.ok
    assert "Installer le plugin" in outcome.text


def test_today_summarizes_recent_runs_and_presets(tmp_path: Path) -> None:
    from engine.core.history import HistoryEntry, HistoryStore

    settings = tmp_path / "settings.json"
    HistoryStore(settings).record(
        HistoryEntry(
            id="abc123abc123",
            started_at="2026-10-06T08:00:00+00:00",
            module="dwg-parts",
            module_name="Liste de pièces",
            inputs={},
            status="succeeded",
            summary="3 lignes",
            outputs=["C:/Sortie/liste.xlsx"],
            duration_ms=10,
        )
    )

    today = describe_today(settings)

    assert today["recent_runs"][0]["feature_name"] == "Liste de pièces"
    assert today["recent_runs"][0]["outputs"] == ["C:/Sortie/liste.xlsx"]
    assert today["presets"] == []


def test_assistant_reads_a_run_and_its_warnings_in_detail(tmp_path: Path) -> None:
    from engine.core.history import HistoryEntry, HistoryStore, HistoryWarning

    settings = tmp_path / "settings.json"
    HistoryStore(settings).record(
        HistoryEntry(
            id="abc123abc123",
            started_at="2026-10-06T08:00:00+00:00",
            module="dwg-parts",
            module_name="Liste de pièces",
            inputs={"files": ["C:/Plans/a.dwg"]},
            status="succeeded",
            summary="3 lignes",
            outputs=["C:/Sortie/liste.xlsx"],
            warnings=[
                HistoryWarning(
                    message="Attribut « REF » absent sur 1 bloc.",
                    file="C:/Plans/a.dwg",
                    location="bloc PANNEAU",
                    hint="Ajoutez l'attribut.",
                )
            ],
            duration_ms=10,
        )
    )

    listed = anyio.run(_toolbox_call, settings, "list_runs", {"limit": 3})
    detail = anyio.run(_toolbox_call, settings, "read_run", {"run_id": "abc123abc123"})
    missing = anyio.run(_toolbox_call, settings, "read_run", {"run_id": "nope"})

    assert listed.ok and "abc123abc123" in listed.text
    assert detail.ok and "bloc PANNEAU" in detail.text and "Ajoutez l'attribut." in detail.text
    assert not missing.ok and "list_runs" in missing.text

import json
from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

from engine.assistant.mcp_server import server_parameters

EXPECTED_TOOLS = {"list_features", "list_presets", "list_templates"}


async def _call_tools(settings: Path, *names: str) -> tuple[set[str], list[CallToolResult]]:
    async with (
        stdio_client(server_parameters(settings)) as (read, write),
        ClientSession(read, write) as session,
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

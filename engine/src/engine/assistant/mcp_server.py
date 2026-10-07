"""Drawflow MCP server (stdio): the tools a local model can call."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp import StdioServerParameters
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from engine.assistant.inspect import inspect_file
from engine.assistant.messages import t
from engine.assistant.tools import (
    describe_features,
    describe_presets,
    describe_run,
    describe_runs,
    describe_templates,
    describe_today,
    help_section,
    help_topics,
    inspect_submission,
    propose_feature_run,
    propose_preset_run,
)
from engine.assistant.tools import (
    propose_column_synonyms as propose_column_synonyms_run,
)
from engine.core.errors import EngineError
from engine.core.registry import discover_modules

SERVER_NAME = "drawflow"
SERVER_INSTRUCTIONS = t("mcp_server.instructions")
# Proposals are read-only too: a run only starts when the user confirms it in the app.
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


def build_server(settings: Path) -> MCPServer:
    server = MCPServer(SERVER_NAME, instructions=SERVER_INSTRUCTIONS, log_level="WARNING")

    @server.tool(description=t("mcp_server.list_features"), annotations=READ_ONLY)
    def list_features() -> dict[str, Any]:
        return _as_tool_result(describe_features)

    @server.tool(description=t("mcp_server.list_presets"), annotations=READ_ONLY)
    def list_presets() -> dict[str, Any]:
        return _as_tool_result(lambda: describe_presets(settings))

    @server.tool(description=t("mcp_server.list_templates"), annotations=READ_ONLY)
    def list_templates() -> dict[str, Any]:
        return _as_tool_result(lambda: describe_templates(settings))

    @server.tool(description=t("mcp_server.read_today"), annotations=READ_ONLY)
    def read_today() -> dict[str, Any]:
        return _as_tool_result(lambda: describe_today(settings))

    @server.tool(
        name="inspect_file", description=t("mcp_server.inspect_file"), annotations=READ_ONLY
    )
    def inspect_file_tool(path: str) -> dict[str, Any]:
        return _as_tool_result(lambda: inspect_file(settings, path))

    @server.tool(description=t("mcp_server.list_runs"), annotations=READ_ONLY)
    def list_runs(limit: int = 5) -> dict[str, Any]:
        return _as_tool_result(lambda: describe_runs(settings, limit))

    @server.tool(description=t("mcp_server.read_run"), annotations=READ_ONLY)
    def read_run(run_id: str) -> dict[str, Any]:
        return _as_tool_result(lambda: describe_run(settings, run_id))

    @server.tool(description=t("mcp_server.list_help_topics"), annotations=READ_ONLY)
    def list_help_topics() -> dict[str, Any]:
        return _as_tool_result(help_topics)

    @server.tool(description=t("mcp_server.read_help"), annotations=READ_ONLY)
    def read_help(topic: str) -> dict[str, Any]:
        return _as_tool_result(lambda: help_section(topic))

    @server.tool(description=t("mcp_server.inspect_submission_headers"), annotations=READ_ONLY)
    def inspect_submission_headers(path: str) -> dict[str, Any]:
        return _as_tool_result(lambda: inspect_submission(settings, path))

    @server.tool(description=t("mcp_server.propose_column_synonyms"), annotations=READ_ONLY)
    def propose_column_synonyms(additions: dict[str, list[str]]) -> dict[str, Any]:
        return _as_tool_result(lambda: propose_column_synonyms_run(settings, additions))

    @server.tool(description=t("mcp_server.propose_preset"), annotations=READ_ONLY)
    def propose_preset(preset_id: str) -> dict[str, Any]:
        return _as_tool_result(lambda: propose_preset_run(settings, preset_id))

    @server.tool(description=t("mcp_server.propose_feature"), annotations=READ_ONLY)
    def propose_feature(feature_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        return _as_tool_result(lambda: propose_feature_run(feature_id, inputs))

    return server


def serve(settings: Path) -> None:
    # On Windows, while the stdio loop blocks reading stdin, an import that probes the console
    # (isatty) waits on the same pipe forever: every module is imported before the loop starts.
    discover_modules()
    import engine.modules.soumission.headers  # noqa: F401  (lazy elsewhere, see tools.py)

    build_server(settings).run("stdio")


def server_parameters(settings: Path) -> StdioServerParameters:
    """How to launch this engine's own MCP server, frozen sidecar or source checkout."""
    if getattr(sys, "frozen", False):
        command, prefix = sys.executable, []
    else:
        command, prefix = sys.executable, ["-m", "engine.cli"]
    arguments = [*prefix, "mcp", "--settings", str(settings)]
    return StdioServerParameters(command=command, args=arguments)


def _as_tool_result(describe: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return describe()
    except EngineError as error:
        details = f"{error.message} {error.hint}" if error.hint else error.message
        raise ToolError(details) from error

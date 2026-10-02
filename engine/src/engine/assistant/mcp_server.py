"""Drawflow MCP server (stdio): the tools a local model can call."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp import StdioServerParameters
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from engine.assistant.tools import describe_features, describe_presets, describe_templates
from engine.core.errors import EngineError

SERVER_NAME = "drawflow"
SERVER_INSTRUCTIONS = (
    "Drawflow automatise le travail d'un dessinateur en façade : listes de pièces depuis des "
    "plans DWG, rapports DOCX depuis des PDF et soumissions. Ces outils décrivent les "
    "fonctionnalités, les préréglages et les modèles disponibles."
)
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


def build_server(settings: Path) -> FastMCP:
    server = FastMCP(SERVER_NAME, instructions=SERVER_INSTRUCTIONS, log_level="WARNING")

    @server.tool(
        description="Liste les fonctionnalités de Drawflow, leur mode d'emploi et leurs entrées.",
        annotations=READ_ONLY,
    )
    def list_features() -> dict[str, Any]:
        return _as_tool_result(describe_features)

    @server.tool(
        description="Liste les préréglages enregistrés (jeux de paramètres prêts à lancer).",
        annotations=READ_ONLY,
    )
    def list_presets() -> dict[str, Any]:
        return _as_tool_result(lambda: describe_presets(settings))

    @server.tool(
        description="Liste les modèles de sortie importés et le modèle par défaut de chaque "
        "fonctionnalité.",
        annotations=READ_ONLY,
    )
    def list_templates() -> dict[str, Any]:
        return _as_tool_result(lambda: describe_templates(settings))

    return server


def serve(settings: Path) -> None:
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

"""Drawflow MCP server (stdio): the tools a local model can call."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp import StdioServerParameters
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from engine.assistant.tools import (
    describe_features,
    describe_presets,
    describe_templates,
    propose_feature_run,
    propose_preset_run,
)
from engine.core.errors import EngineError
from engine.core.registry import discover_modules

SERVER_NAME = "drawflow"
SERVER_INSTRUCTIONS = (
    "Drawflow automatise le travail d'un dessinateur en façade : listes de pièces depuis des "
    "plans DWG, rapports DOCX depuis des PDF et soumissions. Ces outils décrivent les "
    "fonctionnalités, les préréglages et les modèles disponibles, et proposent des lancements "
    "que l'utilisateur confirme."
)
# Proposals are read-only too: a run only starts when the user confirms it in the app.
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

    @server.tool(
        description="Propose de lancer un préréglage. Rien n'est lancé : l'utilisateur voit "
        "une carte et doit cliquer sur Lancer.",
        annotations=READ_ONLY,
    )
    def propose_preset(preset_id: str) -> dict[str, Any]:
        return _as_tool_result(lambda: propose_preset_run(settings, preset_id))

    @server.tool(
        description="Propose de lancer une fonctionnalité avec des entrées conformes à son "
        "inputs_schema (voir list_features). Rien n'est lancé : l'utilisateur voit une carte "
        "et doit cliquer sur Lancer.",
        annotations=READ_ONLY,
    )
    def propose_feature(feature_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        return _as_tool_result(lambda: propose_feature_run(feature_id, inputs))

    return server


def serve(settings: Path) -> None:
    # On Windows, while the stdio loop blocks reading stdin, an import that probes the console
    # (isatty) waits on the same pipe forever: every module is imported before the loop starts.
    discover_modules()
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

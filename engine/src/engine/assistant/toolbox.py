"""MCP tools seen through the OpenAI function-calling format."""

import json
from dataclasses import dataclass
from typing import Any, Protocol

from mcp import ClientSession
from mcp.shared.exceptions import MCPError
from mcp.types import TextContent
from pydantic import ValidationError

from engine.assistant.events import Proposal
from engine.assistant.messages import t

# Keeps one verbose tool answer from filling a small model's context.
MAX_TOOL_OUTPUT_CHARS = 20_000


PROPOSAL_KEY = "proposal"


@dataclass(frozen=True)
class ToolOutcome:
    ok: bool
    text: str
    proposal: Proposal | None = None


class ToolBox(Protocol):
    async def definitions(self) -> list[dict[str, Any]]: ...

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome: ...


class McpToolBox:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def definitions(self) -> list[dict[str, Any]]:
        listed = await self._session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or tool.name,
                    "parameters": tool.input_schema,
                },
            }
            for tool in listed.tools
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        try:
            result = await self._session.call_tool(name, arguments)
        except MCPError as error:
            return ToolOutcome(ok=False, text=t("toolbox.tool_failed", name=name, error=error))
        texts = [part.text for part in result.content if isinstance(part, TextContent)]
        if not texts and result.structured_content is not None:
            texts = [json.dumps(result.structured_content, ensure_ascii=False)]
        proposal = None if result.is_error else _proposal(result.structured_content)
        return ToolOutcome(
            ok=not result.is_error, text=_truncate("\n".join(texts)), proposal=proposal
        )


def _proposal(structured: dict[str, Any] | None) -> Proposal | None:
    if not structured or PROPOSAL_KEY not in structured:
        return None
    try:
        return Proposal.model_validate(structured[PROPOSAL_KEY])
    except ValidationError:
        return None


def _truncate(text: str) -> str:
    if len(text) <= MAX_TOOL_OUTPUT_CHARS:
        return text
    return text[:MAX_TOOL_OUTPUT_CHARS] + t("toolbox.truncated")

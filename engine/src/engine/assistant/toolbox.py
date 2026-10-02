"""MCP tools seen through the OpenAI function-calling format."""

import json
from dataclasses import dataclass
from typing import Any, Protocol

from mcp import ClientSession
from mcp.types import TextContent

# Keeps one verbose tool answer from filling a small model's context.
MAX_TOOL_OUTPUT_CHARS = 20_000
TRUNCATION_NOTICE = "\n[… réponse tronquée]"


@dataclass(frozen=True)
class ToolOutcome:
    ok: bool
    text: str


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
                    "parameters": tool.inputSchema,
                },
            }
            for tool in listed.tools
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        result = await self._session.call_tool(name, arguments)
        texts = [part.text for part in result.content if isinstance(part, TextContent)]
        if not texts and result.structuredContent is not None:
            texts = [json.dumps(result.structuredContent, ensure_ascii=False)]
        return ToolOutcome(ok=not result.isError, text=_truncate("\n".join(texts)))


def _truncate(text: str) -> str:
    if len(text) <= MAX_TOOL_OUTPUT_CHARS:
        return text
    return text[:MAX_TOOL_OUTPUT_CHARS] + TRUNCATION_NOTICE

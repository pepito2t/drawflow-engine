"""NDJSON events of an assistant turn, read by the chat panel."""

import sys
from collections.abc import Callable
from typing import Annotated, Any, Literal, TextIO

from pydantic import BaseModel, ConfigDict, Field

from engine.core.events import ErrorEvent


class _BaseEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TextDeltaEvent(_BaseEvent):
    type: Literal["delta"] = "delta"
    text: str


class ToolCallEvent(_BaseEvent):
    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    arguments: dict[str, Any]


class ToolResultEvent(_BaseEvent):
    type: Literal["tool_result"] = "tool_result"
    id: str
    name: str
    ok: bool


class DoneEvent(_BaseEvent):
    type: Literal["done"] = "done"


AssistantEvent = Annotated[
    TextDeltaEvent | ToolCallEvent | ToolResultEvent | DoneEvent | ErrorEvent,
    Field(discriminator="type"),
]
EmitAssistant = Callable[[AssistantEvent], None]


def make_assistant_emitter(stream: TextIO = sys.stdout) -> EmitAssistant:
    def emit(event: AssistantEvent) -> None:
        stream.write(event.model_dump_json() + "\n")
        stream.flush()

    return emit

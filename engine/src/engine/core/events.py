import sys
from collections.abc import Callable
from typing import Annotated, Literal, TextIO

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _BaseEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ProgressEvent(_BaseEvent):
    type: Literal["progress"] = "progress"
    current: int = Field(ge=0)
    total: int = Field(ge=1)
    message: str = ""


class LogEvent(_BaseEvent):
    type: Literal["log"] = "log"
    message: str


class WarningEvent(_BaseEvent):
    type: Literal["warning"] = "warning"
    message: str
    file: str | None = None


class ResultEvent(_BaseEvent):
    type: Literal["result"] = "result"
    summary: str
    outputs: list[str] = Field(default_factory=list)


class ErrorEvent(_BaseEvent):
    type: Literal["error"] = "error"
    message: str
    file: str | None = None
    hint: str | None = None


Event = Annotated[
    ProgressEvent | LogEvent | WarningEvent | ResultEvent | ErrorEvent,
    Field(discriminator="type"),
]
Emit = Callable[[Event], None]

EVENT_ADAPTER: TypeAdapter[Event] = TypeAdapter(Event)


def to_ndjson_line(event: Event) -> str:
    return event.model_dump_json() + "\n"


def parse_ndjson_line(line: str) -> Event:
    return EVENT_ADAPTER.validate_json(line)


def make_stream_emitter(stream: TextIO = sys.stdout) -> Emit:
    def emit(event: Event) -> None:
        stream.write(to_ndjson_line(event))
        stream.flush()

    return emit

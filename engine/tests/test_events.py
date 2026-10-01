import io
import json

import pytest
from pydantic import ValidationError

from engine.core.events import (
    ErrorEvent,
    ProgressEvent,
    ResultEvent,
    make_stream_emitter,
    parse_ndjson_line,
    to_ndjson_line,
)


def test_event_serializes_to_single_json_line_with_type() -> None:
    line = to_ndjson_line(ProgressEvent(current=1, total=3, message="Fichier é"))

    assert line.endswith("\n")
    assert line.count("\n") == 1
    assert json.loads(line) == {
        "type": "progress",
        "current": 1,
        "total": 3,
        "message": "Fichier é",
    }


def test_round_trip_through_discriminated_union() -> None:
    event = ErrorEvent(message="Fichier illisible", file="C:\\plans\\a.dwg", hint="Réessayez")

    assert parse_ndjson_line(to_ndjson_line(event)) == event


def test_unknown_event_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_ndjson_line('{"type": "unknown", "message": "x"}')


def test_progress_total_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        ProgressEvent(current=0, total=0)


def test_stream_emitter_writes_one_line_per_event() -> None:
    stream = io.StringIO()
    emit = make_stream_emitter(stream)

    emit(ProgressEvent(current=0, total=1))
    emit(ResultEvent(summary="ok"))

    lines = stream.getvalue().splitlines()
    assert [json.loads(line)["type"] for line in lines] == ["progress", "result"]

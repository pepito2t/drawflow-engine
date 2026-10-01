from pathlib import Path

from engine.core.events import Event, LogEvent, ProgressEvent
from engine.modules.hello.schema import HelloInputs
from engine.modules.hello.service import GREETING_FILE_NAME, build_greeting, run


class InMemoryWriter:
    def __init__(self) -> None:
        self.files: dict[Path, str] = {}

    def write_text(self, path: Path, content: str) -> None:
        self.files[path] = content


def test_build_greeting_trims_name() -> None:
    assert build_greeting("  Léa ") == "Bonjour Léa !"


def test_run_writes_greeting_and_reports_progress() -> None:
    events: list[Event] = []
    writer = InMemoryWriter()
    inputs = HelloInputs(name="Léa", output_folder=Path("sortie"))

    result = run(inputs, events.append, writer)

    expected_path = Path("sortie") / GREETING_FILE_NAME
    assert writer.files == {expected_path: "Bonjour Léa !"}
    assert result.outputs == [expected_path]
    assert isinstance(events[0], ProgressEvent)
    assert any(isinstance(event, LogEvent) for event in events)
    last = events[-1]
    assert isinstance(last, ProgressEvent)
    assert last.current == last.total

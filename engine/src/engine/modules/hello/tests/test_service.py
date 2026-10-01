from datetime import datetime
from pathlib import Path

from engine.core.events import Event, LogEvent, ProgressEvent
from engine.modules.hello.schema import HelloInputs
from engine.modules.hello.service import build_file_name, build_greeting, run
from engine.modules.hello.settings import HelloSettings

MOMENT = datetime(2026, 10, 1, 14, 30)


class InMemoryWriter:
    def __init__(self) -> None:
        self.files: dict[Path, str] = {}

    def write_text(self, folder: Path, file_name: str, content: str) -> Path:
        path = folder / file_name
        self.files[path] = content
        return path


def test_build_greeting_trims_name() -> None:
    assert build_greeting("  Léa ") == "Bonjour Léa !"


def test_file_name_follows_the_configured_norm() -> None:
    settings = HelloSettings(file_name_template="{projet}_{type}_{date}")

    assert build_file_name(settings, MOMENT) == "test_20261001.txt"


def test_run_writes_greeting_and_reports_progress() -> None:
    events: list[Event] = []
    writer = InMemoryWriter()
    inputs = HelloInputs(name="Léa", output_folder=Path("sortie"))

    result = run(inputs, events.append, HelloSettings(), writer, MOMENT)

    expected_path = Path("sortie") / "test_20261001-1430.txt"
    assert writer.files == {expected_path: "Bonjour Léa !"}
    assert result.outputs == [expected_path]
    assert isinstance(events[0], ProgressEvent)
    assert any(isinstance(event, LogEvent) for event in events)
    last = events[-1]
    assert isinstance(last, ProgressEvent)
    assert last.current == last.total

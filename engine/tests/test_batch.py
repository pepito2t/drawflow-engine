from operator import methodcaller
from pathlib import Path

import pytest

from engine.core.batch import UNEXPECTED_ITEM_ERROR, process_batch
from engine.core.errors import EngineError
from engine.core.events import Event, ProgressEvent, WarningEvent

read_text = methodcaller("read_text", encoding="utf-8")


def make_files(folder: Path, count: int) -> list[Path]:
    paths = []
    for index in range(count):
        path = folder / f"plan é {index}.txt"
        path.write_text(f"contenu {index}", encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.parametrize("batch_size", [1, 3])
def test_results_keep_input_order(tmp_path: Path, batch_size: int) -> None:
    paths = make_files(tmp_path, 5)
    events: list[Event] = []

    outcome = process_batch(
        paths, read_text, batch_size=batch_size, emit=events.append, label="Lecture"
    )

    assert [path for path, _ in outcome.results] == paths
    assert outcome.results[2][1] == "contenu 2"
    assert outcome.failures == []


@pytest.mark.parametrize("batch_size", [1, 3])
def test_progress_is_emitted_for_every_file(tmp_path: Path, batch_size: int) -> None:
    paths = make_files(tmp_path, 4)
    events: list[Event] = []

    process_batch(paths, read_text, batch_size=batch_size, emit=events.append, label="Lecture")

    progress = [event for event in events if isinstance(event, ProgressEvent)]
    assert [event.current for event in progress] == [1, 2, 3, 4]
    assert all(event.total == 4 for event in progress)


@pytest.mark.parametrize("batch_size", [1, 2])
def test_a_failing_file_does_not_stop_the_batch(tmp_path: Path, batch_size: int) -> None:
    paths = make_files(tmp_path, 2)
    missing = tmp_path / "absent.txt"
    events: list[Event] = []

    outcome = process_batch(
        [paths[0], missing, paths[1]],
        read_text,
        batch_size=batch_size,
        emit=events.append,
        label="Lecture",
    )

    assert [path for path, _ in outcome.results] == paths
    assert [failure.path for failure in outcome.failures] == [missing]
    warnings = [event for event in events if isinstance(event, WarningEvent)]
    assert [warning.file for warning in warnings] == [str(missing)]
    assert warnings[0].message == UNEXPECTED_ITEM_ERROR
    assert warnings[0].hint is not None


def test_engine_errors_keep_their_readable_message(tmp_path: Path) -> None:
    def worker(path: Path) -> str:
        raise EngineError("Plan illisible.", file=path, hint="Ré-exportez-le depuis AutoCAD.")

    events: list[Event] = []
    outcome = process_batch(
        [tmp_path / "a.dwg"], worker, batch_size=1, emit=events.append, label="Lecture"
    )

    assert outcome.failures[0].message == "Plan illisible."
    [warning] = [event for event in events if isinstance(event, WarningEvent)]
    assert warning.hint == "Ré-exportez-le depuis AutoCAD."


def test_empty_batch_returns_empty_outcome() -> None:
    events: list[Event] = []

    outcome = process_batch([], read_text, batch_size=4, emit=events.append, label="Lecture")

    assert outcome.results == []
    assert events == []

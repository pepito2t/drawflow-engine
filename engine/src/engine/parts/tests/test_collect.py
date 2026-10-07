from pathlib import Path

import pytest

from engine.core.collect import FileCollectionError
from engine.core.events import Event, WarningEvent
from engine.parts.collect import collect_plans


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    (tmp_path / "Façades").mkdir()
    (tmp_path / "Façades" / "Nord.DWG").write_bytes(b"")
    (tmp_path / "Façades" / "notes.txt").write_text("", encoding="utf-8")
    (tmp_path / "Façades" / "Détails").mkdir()
    (tmp_path / "Façades" / "Détails" / "angle.dxf").write_text("", encoding="utf-8")
    return tmp_path


def test_collects_plans_recursively_case_insensitively(tree: Path) -> None:
    events: list[Event] = []

    plans = collect_plans([], [tree / "Façades"], recursive=True, emit=events.append)

    assert [plan.name for plan in plans] == ["angle.dxf", "Nord.DWG"]


def test_non_recursive_scan_stays_at_top_level(tree: Path) -> None:
    plans = collect_plans([], [tree / "Façades"], recursive=False, emit=lambda _: None)

    assert [plan.name for plan in plans] == ["Nord.DWG"]


def test_duplicates_between_files_and_folders_are_removed(tree: Path) -> None:
    nord = tree / "Façades" / "Nord.DWG"

    plans = collect_plans([nord], [tree / "Façades"], recursive=False, emit=lambda _: None)

    assert plans == [nord]


def test_non_plan_files_are_ignored_with_a_warning(tree: Path) -> None:
    events: list[Event] = []
    notes = tree / "Façades" / "notes.txt"

    collect_plans([notes, tree / "Façades" / "Nord.DWG"], [], recursive=True, emit=events.append)

    assert [event.file for event in events if isinstance(event, WarningEvent)] == [str(notes)]


def test_missing_folder_is_reported(tmp_path: Path) -> None:
    with pytest.raises(FileCollectionError) as caught:
        collect_plans([], [tmp_path / "absent"], recursive=True, emit=lambda _: None)

    assert caught.value.file == tmp_path / "absent"


def test_no_plan_found_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(FileCollectionError):
        collect_plans([], [tmp_path], recursive=True, emit=lambda _: None)


def test_missing_file_is_a_warning_with_a_hint(tree: Path) -> None:
    events: list[Event] = []
    gone = tree / "Façades" / "Disparu.dwg"

    plans = collect_plans(
        [gone, tree / "Façades" / "Nord.DWG"], [], recursive=True, emit=events.append
    )

    assert [plan.name for plan in plans] == ["Nord.DWG"]
    [warning] = [event for event in events if isinstance(event, WarningEvent)]
    assert warning.file == str(gone) and warning.hint is not None

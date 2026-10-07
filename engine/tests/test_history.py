import json
from pathlib import Path

import pytest

from engine.core.contract import ModuleResult
from engine.core.errors import EngineError, InvalidInputError
from engine.core.events import Emit, Event, LogEvent, WarningEvent
from engine.core.history import (
    MAX_ENTRIES,
    HistoryEntry,
    HistoryError,
    HistoryStore,
    handle_history,
    run_with_history,
)
from engine.core.registry import discover_modules

MODULE = discover_modules()["dwg-parts"]
INPUTS = {"files": ["C:/Plans/a.dwg"], "project": "Façade", "output_folder": "C:/Sortie"}


def _entry(index: int) -> HistoryEntry:
    return HistoryEntry(
        id=f"{index:012x}",
        started_at="2026-10-06T10:00:00+00:00",
        module="dwg-parts",
        module_name="Liste de pièces",
        inputs=INPUTS,
        status="succeeded",
        summary=f"run {index}",
        duration_ms=10,
    )


def test_successful_run_is_recorded_with_outputs_and_warnings(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "settings.json")
    seen: list[Event] = []

    def run(emit: Emit) -> ModuleResult:
        emit(WarningEvent(message="Bloc inconnu"))
        emit(LogEvent(message="Écriture"))
        return ModuleResult(summary="2 pièces", outputs=[Path("C:/Sortie/liste.xlsx")])

    result = run_with_history(store, MODULE, INPUTS, seen.append, run)

    [entry] = store.entries()
    assert result.summary == "2 pièces"
    assert entry.status == "succeeded"
    assert entry.outputs == [str(Path("C:/Sortie/liste.xlsx"))]
    assert [warning.message for warning in entry.warnings] == ["Bloc inconnu"]
    assert entry.inputs == INPUTS
    assert entry.module_name == MODULE.manifest.name
    assert [event.type for event in seen] == ["warning", "log"]


def test_failed_run_is_recorded_then_the_error_still_surfaces(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "settings.json")

    def failing(_: object) -> ModuleResult:
        raise EngineError("Aucun plan n'a pu être lu.")

    with pytest.raises(EngineError, match="Aucun plan"):
        run_with_history(store, MODULE, INPUTS, lambda _: None, failing)

    [entry] = store.entries()
    assert entry.status == "failed"
    assert entry.error == "Aucun plan n'a pu être lu."


def test_internal_error_is_recorded_as_failed_then_still_surfaces(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "settings.json")

    def crashing(_: object) -> ModuleResult:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        run_with_history(store, MODULE, INPUTS, lambda _: None, crashing)

    [entry] = store.entries()
    assert entry.status == "failed"
    assert entry.error == "Erreur interne inattendue."


def test_without_a_store_the_run_is_untouched(tmp_path: Path) -> None:
    result = run_with_history(
        None, MODULE, INPUTS, lambda _: None, lambda _: ModuleResult(summary="ok")
    )

    assert result.summary == "ok"


def test_newest_first_and_capped(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "settings.json")
    for index in range(MAX_ENTRIES + 5):
        store.record(_entry(index))

    entries = store.entries()
    assert len(entries) == MAX_ENTRIES
    assert entries[0].summary == f"run {MAX_ENTRIES + 4}"


def test_remove_clear_and_list_through_the_handler(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    store = HistoryStore(settings)
    store.record(_entry(1))
    store.record(_entry(2))

    assert len(handle_history("list", settings, {})["entries"]) == 2
    handle_history("remove", settings, {"id": _entry(1).id})
    assert [entry.summary for entry in store.entries()] == ["run 2"]
    handle_history("clear", settings, {})
    assert store.entries() == []
    with pytest.raises(InvalidInputError):
        handle_history("remove", settings, {})


def test_unreadable_history_is_reported_not_overwritten(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    history = tmp_path / "history.json"
    history.write_text("pas du json", encoding="utf-8")

    with pytest.raises(HistoryError, match="illisible"):
        HistoryStore(settings).entries()
    assert history.read_text(encoding="utf-8") == "pas du json"
    assert json.loads('{"ok": true}')["ok"]


def test_entries_with_plain_text_warnings_from_older_versions_still_load(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    legacy = {**_entry(1).model_dump(mode="json"), "warnings": ["Bloc inconnu"]}
    (tmp_path / "history.json").write_text(json.dumps([legacy]), encoding="utf-8")

    [entry] = HistoryStore(settings).entries()

    assert entry.warnings[0].message == "Bloc inconnu"
    assert entry.warnings[0].location is None


def test_unwritable_history_warns_instead_of_failing_the_run(tmp_path: Path) -> None:
    (tmp_path / "history.json").mkdir()
    store = HistoryStore(tmp_path / "settings.json")
    seen: list[Event] = []

    result = run_with_history(
        store, MODULE, INPUTS, seen.append, lambda _: ModuleResult(summary="2 pièces")
    )

    assert result.summary == "2 pièces"
    [warning] = seen
    assert isinstance(warning, WarningEvent)
    assert warning.message == "Impossible d'enregistrer l'historique."


def test_unreadable_history_warns_and_the_failure_still_surfaces(tmp_path: Path) -> None:
    (tmp_path / "history.json").write_text("pas du json", encoding="utf-8")
    store = HistoryStore(tmp_path / "settings.json")
    seen: list[Event] = []

    def failing(_: object) -> ModuleResult:
        raise EngineError("Aucun plan n'a pu être lu.")

    with pytest.raises(EngineError, match="Aucun plan"):
        run_with_history(store, MODULE, INPUTS, seen.append, failing)

    assert [event.type for event in seen] == ["warning"]

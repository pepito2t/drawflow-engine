import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from engine.core.contract import ModuleResult
from engine.core.events import Event, WarningEvent
from engine.core.fields import ui_field
from engine.core.history import HistoryStore, UsageCounters, handle_history, run_with_history
from engine.core.registry import discover_modules
from engine.core.stats import StatsError, StatsStore, count_files

MODULE = discover_modules()["dwg-parts"]
INPUTS = {
    "files": ["C:/Plans/a.dwg", "C:/Plans/b.dwg"],
    "project": "Façade",
    "output_folder": "C:/Sortie",
}
MINUTES_PER_FILE = 5


def _run_once(tmp_path: Path, events: list[Event]) -> None:
    settings = tmp_path / "settings.json"
    run_with_history(
        HistoryStore(settings),
        MODULE,
        INPUTS,
        events.append,
        lambda _: ModuleResult(summary="2 lignes", outputs=[tmp_path / "liste.xlsx"]),
        counters=UsageCounters(StatsStore(settings), MINUTES_PER_FILE),
    )


class _Inputs(BaseModel):
    files: list[str] = ui_field("files", label="Plans", default=[])
    report: str | None = ui_field("file", label="Rapport", default=None)
    template: str | None = ui_field("template", label="Modèle", default=None)
    folder: str | None = ui_field("folder", label="Dossier", default=None)
    project: str = ui_field("text", label="Projet", default="")


def test_only_file_fields_of_the_schema_are_counted() -> None:
    inputs = {
        "files": ["C:/Plans/a.dwg", "C:/Plans/b.dwg"],
        "report": "C:/r.pdf",
        "template": "C:/Modèles/Liste.xlsx",
        "folder": "C:/Plans",
        "project": "Tour 1.2",
    }

    assert count_files(_Inputs, inputs) == 3
    assert count_files(MODULE.inputs_model, INPUTS) == 2


def test_successful_runs_accumulate_per_feature(tmp_path: Path) -> None:
    events: list[Event] = []
    _run_once(tmp_path, events)
    _run_once(tmp_path, events)

    stats = handle_history("stats", tmp_path / "settings.json", {})

    assert stats["since"] is not None
    assert stats["features"] == [
        {
            "module": "dwg-parts",
            "module_name": "Liste de pièces",
            "runs": 2,
            "files": 4,
            "minutes_saved": 4 * MINUTES_PER_FILE,
        }
    ]
    assert not any(isinstance(event, WarningEvent) for event in events)


def test_broken_counter_file_warns_but_keeps_the_run(tmp_path: Path) -> None:
    (tmp_path / "stats.json").write_text("{", encoding="utf-8")
    events: list[Event] = []

    _run_once(tmp_path, events)

    warnings = [event for event in events if isinstance(event, WarningEvent)]
    assert len(warnings) == 1 and "compteurs" in warnings[0].message
    assert len(HistoryStore(tmp_path / "settings.json").entries()) == 1
    with pytest.raises(StatsError):
        StatsStore(tmp_path / "settings.json").read()


def test_missing_file_means_empty_counters(tmp_path: Path) -> None:
    stats = handle_history("stats", tmp_path / "settings.json", {})

    assert stats == {"since": None, "features": []}
    assert not (tmp_path / "stats.json").exists()
    StatsStore(tmp_path / "settings.json").record("pdf-report", "Rapport", 1, MINUTES_PER_FILE)
    assert (
        json.loads((tmp_path / "stats.json").read_text(encoding="utf-8"))["features"][0]["files"]
        == 1
    )

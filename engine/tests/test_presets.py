import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.core.presets import PresetError, PresetStore
from engine.core.registry import get_module


@pytest.fixture
def store(tmp_path: Path) -> PresetStore:
    return PresetStore(tmp_path / "config" / "settings.json")


def inputs(tmp_path: Path) -> dict[str, object]:
    return {
        "folders": [str(tmp_path / "Plans")],
        "project": "Tour B",
        "output_folder": str(tmp_path / "Sortie"),
    }


def test_saved_presets_are_listed_with_their_module(tmp_path: Path, store: PresetStore) -> None:
    preset = store.save(get_module("dwg-parts"), " Tour B - façades ", inputs(tmp_path))

    assert store.presets() == [preset]
    assert preset.name == "Tour B - façades"
    assert preset.module == "dwg-parts"


def test_saving_with_an_id_updates_in_place(tmp_path: Path, store: PresetStore) -> None:
    preset = store.save(get_module("dwg-parts"), "Tour B", inputs(tmp_path))

    updated = store.save(get_module("dwg-parts"), "Tour B bis", inputs(tmp_path), preset.id)

    assert [item.name for item in store.presets()] == ["Tour B bis"]
    assert updated.id == preset.id


def test_names_are_unique_case_insensitively(tmp_path: Path, store: PresetStore) -> None:
    store.save(get_module("dwg-parts"), "Tour B", inputs(tmp_path))

    with pytest.raises(PresetError):
        store.save(get_module("pdf-report"), "tour b", inputs(tmp_path))


def test_incomplete_forms_are_refused_with_the_field_label(
    tmp_path: Path, store: PresetStore
) -> None:
    with pytest.raises(PresetError) as caught:
        store.save(get_module("dwg-parts"), "Vide", {"project": "x"})

    assert "Dossier de sortie" in caught.value.message


def test_remove(tmp_path: Path, store: PresetStore) -> None:
    preset = store.save(get_module("dwg-parts"), "Tour B", inputs(tmp_path))

    store.remove(preset.id)

    assert store.presets() == []


def test_corrupted_file_is_reported_and_kept(store: PresetStore) -> None:
    store.path.parent.mkdir(parents=True)
    store.path.write_text("{oops", encoding="utf-8")

    with pytest.raises(PresetError):
        store.presets()

    assert store.path.read_text(encoding="utf-8") == "{oops"


def test_cli_saves_and_lists(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({"name": "Tour B", "module": "soumission", "inputs": inputs(tmp_path)}),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "engine.cli",
            "presets",
            "save",
            "--settings",
            str(settings),
            "--input",
            str(request),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )

    [preset] = json.loads(completed.stdout)["presets"]
    assert preset["name"] == "Tour B"

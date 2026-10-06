import json
import zipfile
from pathlib import Path

import pytest
from openpyxl import Workbook

from engine.core.errors import InvalidSettingsError
from engine.core.presets import PresetStore
from engine.core.profile import export_profile, import_profile, read_profile
from engine.core.registry import discover_modules
from engine.core.settings import load_general_settings, save_settings
from engine.core.templates import TemplateLibrary, TemplateUser

MODULES = discover_modules()
APP_VERSION = "0.17.0"
NEWER_VERSION = "0.18.0"


def _workstation(root: Path) -> Path:
    settings = root / "config" / "settings.json"
    save_settings(settings, {"general": {"batch_size": 7}}, MODULES)
    PresetStore(settings).save(
        MODULES["dwg-parts"],
        "Façade nord",
        {"files": ["C:/Plans/a.dwg"], "project": "Nord", "output_folder": "C:/Sortie"},
    )
    workbook = Workbook()
    workbook.save(root / "Liste entreprise.xlsx")
    library = TemplateLibrary(settings)
    template = library.import_file(root / "Liste entreprise.xlsx")
    library.set_default(TemplateUser("dwg-parts", "Liste de pièces", "xlsx"), template.id)
    return settings


def test_profile_round_trip_restores_settings_presets_and_templates(tmp_path: Path) -> None:
    source = _workstation(tmp_path / "poste A")
    archive = tmp_path / "Profil é.zip"
    exported = export_profile(source, archive, MODULES, APP_VERSION)
    target = tmp_path / "poste B" / "settings.json"

    preview = read_profile(archive, target, MODULES, APP_VERSION)
    imported = import_profile(archive, target, MODULES, APP_VERSION)

    assert exported["presets"] == 1 and exported["templates"] == 1
    assert preview["app_version"] == APP_VERSION
    assert preview["presets"] == ["Façade nord"] and preview["templates"] == [
        "Liste entreprise.xlsx"
    ]
    assert preview["replaced_presets"] == 0 and preview["replaced_templates"] == []
    assert imported["sections"] == exported["sections"]
    assert load_general_settings(target).batch_size == 7
    assert [preset.name for preset in PresetStore(target).presets()] == ["Façade nord"]
    assert TemplateLibrary(target).default_for("dwg-parts") is not None


def test_import_replaces_existing_presets_and_reports_it(tmp_path: Path) -> None:
    source = _workstation(tmp_path / "A")
    target = _workstation(tmp_path / "B")
    PresetStore(target).save(
        MODULES["dwg-parts"],
        "Ancien",
        {"files": ["C:/Plans/b.dwg"], "project": "X", "output_folder": "C:/Sortie"},
    )
    archive = tmp_path / "profil.zip"
    export_profile(source, archive, MODULES, APP_VERSION)

    preview = read_profile(archive, target, MODULES, APP_VERSION)
    import_profile(archive, target, MODULES, APP_VERSION)

    assert preview["replaced_presets"] == 2
    assert preview["replaced_templates"] == ["Liste entreprise.xlsx"]
    assert [preset.name for preset in PresetStore(target).presets()] == ["Façade nord"]


def test_newer_profiles_and_foreign_files_are_refused(tmp_path: Path) -> None:
    source = _workstation(tmp_path / "A")
    archive = tmp_path / "profil.zip"
    export_profile(source, archive, MODULES, NEWER_VERSION)
    target = tmp_path / "B" / "settings.json"

    with pytest.raises(InvalidSettingsError, match="plus récent"):
        read_profile(archive, target, MODULES, APP_VERSION)
    with pytest.raises(InvalidSettingsError, match="pas un profil"):
        read_profile(tmp_path / "A" / "Liste entreprise.xlsx", target, MODULES, APP_VERSION)
    assert not target.exists()


def test_profile_with_invalid_settings_changes_nothing(tmp_path: Path) -> None:
    archive = tmp_path / "profil.zip"
    with zipfile.ZipFile(archive, "w") as broken:
        manifest = {
            "format": "drawflow-profile",
            "version": 1,
            "sections": {"general": {"batch_size": 0}},
        }
        broken.writestr("profile.json", json.dumps(manifest))
        broken.writestr("presets.json", "[]")
    target = _workstation(tmp_path / "B")

    with pytest.raises(InvalidSettingsError, match="Général"):
        import_profile(archive, target, MODULES, APP_VERSION)

    assert load_general_settings(target).batch_size == 7

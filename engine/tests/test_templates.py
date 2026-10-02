import json
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook

from engine.core.templates import TemplateError, TemplateLibrary, TemplateUser

PARTS = TemplateUser("dwg-parts", "Liste de pièces", "xlsx")
REPORT = TemplateUser("pdf-report", "Rapport", "docx")


def workbook(path: Path) -> Path:
    Workbook().save(path)
    return path


@pytest.fixture
def library(tmp_path: Path) -> TemplateLibrary:
    return TemplateLibrary(tmp_path / "config" / "settings.json")


def test_import_copies_the_file_into_the_library(tmp_path: Path, library: TemplateLibrary) -> None:
    source = workbook(tmp_path / "Liste entreprise é.xlsx")

    imported = library.import_file(source)

    assert imported.id == "Liste entreprise é.xlsx"
    assert imported.kind == "xlsx"
    assert (library.folder / imported.id).is_file()
    assert source.is_file()


def test_same_name_is_imported_under_a_new_name(tmp_path: Path, library: TemplateLibrary) -> None:
    source = workbook(tmp_path / "modèle.xlsx")

    library.import_file(source)
    second = library.import_file(source)

    assert second.id == "modèle (2).xlsx"


@pytest.mark.parametrize("name", ["ancien.xls", "notes.txt"])
def test_unsupported_formats_are_rejected(
    tmp_path: Path, library: TemplateLibrary, name: str
) -> None:
    source = tmp_path / name
    source.write_text("x", encoding="utf-8")

    with pytest.raises(TemplateError):
        library.import_file(source)


def test_corrupted_template_is_rejected(tmp_path: Path, library: TemplateLibrary) -> None:
    source = tmp_path / "cassé.xlsx"
    source.write_text("pas un zip", encoding="utf-8")

    with pytest.raises(TemplateError):
        library.import_file(source)


def test_default_must_match_the_feature_kind(tmp_path: Path, library: TemplateLibrary) -> None:
    imported = library.import_file(workbook(tmp_path / "liste.xlsx"))

    library.set_default(PARTS, imported.id)
    with pytest.raises(TemplateError):
        library.set_default(REPORT, imported.id)

    assert library.default_for("dwg-parts") == library.folder / "liste.xlsx"
    assert library.default_for("pdf-report") is None


def test_removing_a_template_clears_its_default(tmp_path: Path, library: TemplateLibrary) -> None:
    imported = library.import_file(workbook(tmp_path / "liste.xlsx"))
    library.set_default(PARTS, imported.id)

    library.remove(imported.id)

    assert library.templates() == []
    assert library.defaults() == {}


def test_template_ids_cannot_escape_the_library(library: TemplateLibrary) -> None:
    with pytest.raises(TemplateError):
        library.remove("../settings.json")


def test_cli_lists_features_accepting_templates(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"

    completed = subprocess.run(
        [sys.executable, "-m", "engine.cli", "templates", "list", "--settings", str(settings)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )

    modules = json.loads(completed.stdout)["modules"]
    assert [(module["id"], module["kind"]) for module in modules] == [
        ("dwg-parts", "xlsx"),
        ("pdf-report", "docx"),
    ]

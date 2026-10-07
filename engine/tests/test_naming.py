from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from engine.core.naming import (
    PARTIAL_SUFFIX,
    FileNameTemplate,
    OutputFolderError,
    naming_values,
    output_target,
    render_file_name,
    unique_output_path,
    validate_template,
    writing_output,
)
from engine.core.shutdown import hooks

MOMENT = datetime(2026, 10, 1, 9, 5)


class TemplateHolder(BaseModel):
    template: FileNameTemplate


def test_renders_all_variables() -> None:
    values = naming_values(MOMENT, projet="Tour B", type="liste-pieces", indice="C", source="F01")

    name = render_file_name("{projet}_{type}_{indice}_{date}-{heure}", values, "xlsx")

    assert name == "Tour B_liste-pieces_C_20261001-0905.xlsx"


def test_missing_values_leave_no_stray_separators() -> None:
    name = render_file_name(
        "{projet}_{type}__{indice}_{date}", naming_values(MOMENT, type="rapport"), ".docx"
    )

    assert name == "rapport_20261001.docx"


def test_forbidden_characters_in_values_are_replaced() -> None:
    name = render_file_name("{projet}", {"projet": 'A/B:C*"D'}, "xlsx")

    assert name == "A-B-C-D.xlsx"


@pytest.mark.parametrize("reserved", ["CON", "nul", "COM1", "lpt9"])
def test_reserved_windows_names_are_suffixed(reserved: str) -> None:
    assert render_file_name("{projet}", {"projet": reserved}, "txt") == f"{reserved}_.txt"


def test_empty_result_falls_back_to_default_stem() -> None:
    assert render_file_name("{projet}", {}, "xlsx") == "export.xlsx"


def test_long_names_are_truncated() -> None:
    name = render_file_name("{projet}", {"projet": "x" * 400}, "xlsx")

    assert len(Path(name).stem) == 150


@pytest.mark.parametrize(
    ("template", "reason"),
    [
        ("", "vide"),
        ("{client}_{date}", "variable inconnue {client}"),
        ("{date:%Y}", "option de format"),
        ("{date!r}", "option de format"),
        ("liste{", "accolades"),
        ("a/b_{date}", "caractères interdits"),
    ],
)
def test_invalid_templates_are_rejected_with_a_reason(template: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_template(template)


def test_template_type_validates_in_models() -> None:
    with pytest.raises(ValidationError):
        TemplateHolder(template="{inconnu}")
    assert TemplateHolder(template="{type}_{date}").template == "{type}_{date}"


def test_unique_output_path_never_overwrites(tmp_path: Path) -> None:
    (tmp_path / "liste.xlsx").write_text("", encoding="utf-8")
    (tmp_path / "liste (2).xlsx").write_text("", encoding="utf-8")

    assert unique_output_path(tmp_path, "liste.xlsx") == tmp_path / "liste (3).xlsx"
    assert unique_output_path(tmp_path, "autre.xlsx") == tmp_path / "autre.xlsx"


def test_unique_output_path_reserves_the_name_for_concurrent_runs(tmp_path: Path) -> None:
    workers = 8

    with ThreadPoolExecutor(max_workers=workers) as pool:
        paths = list(pool.map(lambda _: unique_output_path(tmp_path, "liste.xlsx"), range(workers)))

    assert len(set(paths)) == workers
    assert all(path.exists() for path in paths)


def test_unique_output_path_creates_the_folder_and_reports_an_unwritable_one(
    tmp_path: Path,
) -> None:
    assert unique_output_path(tmp_path / "nouveau", "liste.xlsx").parent.is_dir()

    blocked = tmp_path / "fichier"
    blocked.write_text("", encoding="utf-8")
    with pytest.raises(OutputFolderError, match="inaccessible") as caught:
        unique_output_path(blocked / "sous-dossier", "liste.xlsx")
    assert caught.value.file == blocked / "sous-dossier"


def test_writing_output_takes_the_reserved_name_only_once_complete(tmp_path: Path) -> None:
    target = unique_output_path(tmp_path, "liste.xlsx")

    with writing_output(target) as draft:
        assert draft == tmp_path / f"liste.xlsx{PARTIAL_SUFFIX}"
        draft.write_text("contenu", encoding="utf-8")
        assert target.stat().st_size == 0

    assert target.read_text(encoding="utf-8") == "contenu"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["liste.xlsx"]


def test_writing_output_leaves_nothing_behind_on_failure(tmp_path: Path) -> None:
    target = unique_output_path(tmp_path, "liste.xlsx")

    with pytest.raises(RuntimeError), writing_output(target) as draft:
        draft.write_text("à moitié", encoding="utf-8")
        raise RuntimeError("export impossible")

    assert list(tmp_path.iterdir()) == []


def test_writing_output_leaves_nothing_behind_when_the_run_is_cancelled(tmp_path: Path) -> None:
    target = unique_output_path(tmp_path, "liste.xlsx")

    with writing_output(target) as draft:
        draft.write_text("à moitié", encoding="utf-8")
        hooks.trigger()
        assert list(tmp_path.iterdir()) == []
        draft.write_text("fin", encoding="utf-8")

    assert target.read_text(encoding="utf-8") == "fin"


def test_output_target_renders_then_reserves(tmp_path: Path) -> None:
    target = output_target(tmp_path, "{projet}_{type}", {"projet": "A", "type": "liste"}, "xlsx")

    assert target == tmp_path / "A_liste.xlsx"
    assert target.exists()

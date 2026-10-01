from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from engine.core.naming import (
    FileNameTemplate,
    naming_values,
    render_file_name,
    unique_output_path,
    validate_template,
)

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

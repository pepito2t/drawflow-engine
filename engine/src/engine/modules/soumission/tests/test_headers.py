import json
from io import BytesIO
from pathlib import Path

import pytest

from engine.core.errors import InvalidInputError
from engine.modules.soumission.headers import add_synonyms, inspect_headers, validate_additions
from engine.modules.soumission.reader import header_candidates, read_workbook
from engine.modules.soumission.settings import SoumissionSettings, synonyms_of
from engine.modules.soumission.tests.workbooks import submission_bytes


def test_header_candidates_rank_rows_by_how_many_texts_they_hold() -> None:
    rows: list[list[object]] = [
        ["Titre"],
        ["Pos.", "Désignation", "Qté"],
        [None, "Note", "x"],
        [1, 2, 3],
    ]

    candidates = header_candidates(rows)

    assert [(c.row, c.texts) for c in candidates] == [
        (1, ["Pos.", "Désignation", "Qté"]),
        (2, ["Note", "x"]),
    ]


def test_unrecognized_file_tells_which_headers_it_found() -> None:
    only_position = SoumissionSettings(columns=SoumissionSettings().columns[:1])

    content = read_workbook(BytesIO(submission_bytes()), "offre.xlsx", only_position)

    assert content.tables == []
    location = content.warnings[-1].location
    assert location is not None and "Désignation" in location


def test_inspect_lists_candidates_and_what_is_already_recognized(tmp_path: Path) -> None:
    path = tmp_path / "offre.xlsx"
    path.write_bytes(submission_bytes())

    report = inspect_headers(path, SoumissionSettings())

    sheet = report["sheets"][0]
    assert sheet["sheet"] == "Offre"
    assert sheet["candidates"][0]["texts"][:2] == ["Pos.", "Désignation"]
    assert sheet["recognized"]["Désignation"] == "Désignation"
    assert any(column["key"] == "Quantité" for column in report["columns"])


def test_inspect_refuses_other_files(tmp_path: Path) -> None:
    other = tmp_path / "notes.txt"
    other.write_text("x", encoding="utf-8")

    with pytest.raises(InvalidInputError, match="XLSX et PDF"):
        inspect_headers(other, SoumissionSettings())


def test_additions_keep_only_new_names_for_existing_columns() -> None:
    settings = SoumissionSettings()

    cleaned = validate_additions(settings, {"Quantité": ["Nbre", "qté", " Nbre "], "Unité": []})

    assert cleaned == {"Quantité": ["Nbre"]}
    with pytest.raises(InvalidInputError, match="n'existe pas"):
        validate_additions(settings, {"Inconnue": ["x"]})
    with pytest.raises(InvalidInputError, match="Aucun"):
        validate_additions(settings, {"Quantité": ["qté"]})


def test_add_synonyms_persists_them_next_to_the_existing_ones(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"

    added = add_synonyms(settings_file, {"Quantité": ["Nbre"], "Total": ["Somme"]})

    assert added == {"added": {"Quantité": ["Nbre"], "Total": ["Somme"]}}
    document = json.loads(settings_file.read_text(encoding="utf-8"))
    stored = document["modules"]["soumission"]["columns"]
    quantity = next(column for column in stored if column["key"] == "Quantité")
    assert quantity["value"].endswith(";Nbre")
    reloaded = SoumissionSettings.model_validate({"columns": stored})
    assert "Somme" in synonyms_of(next(c for c in reloaded.columns if c.key == "Total"))

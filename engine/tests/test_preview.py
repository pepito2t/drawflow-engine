from pathlib import Path

from engine.core.contract import ModuleResult
from engine.core.history import HistoryStore, run_with_history
from engine.core.registry import discover_modules
from engine.modules.dwg_parts.aggregation import PartLine
from engine.modules.dwg_parts.service import PartsList, preview_table
from engine.modules.soumission.preview import preview_table as preview_submissions
from engine.modules.soumission.reader import SubmissionTable


def test_parts_preview_points_out_empty_cells() -> None:
    parts = PartsList(
        headers=("Repère", "Longueur"),
        lines=[
            PartLine(("P-1", "1200"), 2.0, ("a.dwg",)),
            PartLine(("P-2", ""), 1.5, ("a.dwg", "b.dwg")),
        ],
        warnings=[],
    )

    table = preview_table(parts)

    assert table.headers == ["Repère", "Longueur", "Quantité", "Plans"]
    assert table.rows[0].cells == ["P-1", "1200", "2", "a.dwg"]
    assert table.rows[0].issues == []
    assert table.rows[1].cells == ["P-2", "", "1.5", "a.dwg, b.dwg"]
    assert table.rows[1].issues == ["Colonne « Longueur » vide"]
    assert table.total == 2


def test_submission_preview_points_out_amounts_kept_as_text() -> None:
    tables = [
        SubmissionTable(
            "offre.xlsx",
            "Offre",
            [
                {"Position": "1.1", "Quantité": 3.0, "Prix unitaire": 10.0},
                {"Position": "1.2", "Quantité": "forfait", "Prix unitaire": 2000.0},
            ],
        )
    ]

    table = preview_submissions(tables, ["Position", "Quantité", "Prix unitaire"], ["Quantité"])

    assert table.headers[-2:] == ["Fichier source", "Feuille"]
    assert table.rows[1].cells[:2] == ["1.2", "forfait"]
    assert table.rows[1].issues == ["Montant illisible : colonne « Quantité »"]
    assert table.rows[0].issues == []
    assert table.total == 2


def test_previews_are_not_written_to_the_history(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "settings.json")
    module = discover_modules()["dwg-parts"]

    run_with_history(
        store, module, {}, lambda _: None, lambda _: ModuleResult(summary="Aperçu", preview=True)
    )

    assert store.entries() == []

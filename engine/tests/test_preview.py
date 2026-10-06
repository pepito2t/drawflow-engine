from pathlib import Path

from engine.core.contract import ModuleResult
from engine.core.history import HistoryStore, run_with_history
from engine.core.registry import discover_modules
from engine.modules.dwg_parts.service import merge_projects, preview_table, total_of
from engine.modules.soumission.preview import preview_table as preview_submissions
from engine.modules.soumission.reader import SubmissionTable
from engine.parts.aggregation import PartLine
from engine.parts.listing import PartsList


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


def test_several_projects_get_a_project_column_and_a_grand_total() -> None:
    headers = ("Repère", "Longueur")
    tour_a = PartsList(headers, [PartLine(("P-1", "1200"), 2.0, ("a.dwg",))], [])
    tour_b = PartsList(
        headers,
        [PartLine(("P-1", "1200"), 3.0, ("b.dwg",)), PartLine(("P-2", "900"), 1.0, ("b.dwg",))],
        [],
    )

    merged = merge_projects([("Tour A", tour_a), ("Tour B", tour_b)])
    total = total_of([("Tour A", tour_a), ("Tour B", tour_b)])

    assert merged.headers == ("Projet", "Repère", "Longueur")
    assert [line.values for line in merged.lines] == [
        ("Tour A", "P-1", "1200"),
        ("Tour B", "P-1", "1200"),
        ("Tour B", "P-2", "900"),
    ]
    assert total.headers == headers
    assert [(line.values, line.quantity, line.sources) for line in total.lines] == [
        (("P-1", "1200"), 5.0, ("a.dwg", "b.dwg")),
        (("P-2", "900"), 1.0, ("b.dwg",)),
    ]

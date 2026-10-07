from pathlib import Path

from engine.modules.pdf_report.settings import PdfReportSettings
from engine.modules.pdf_report.worker import extract_plan
from engine.testing.pdf import PdfSpec, TextItem, write_pdf


def test_references_are_collected_across_pages_and_deduplicated(tmp_path: Path) -> None:
    pdf = write_pdf(
        tmp_path / "plan.pdf",
        PdfSpec(
            pages=[
                [TextItem(60, 100, "Voir P-1200 et EQ-40")],
                [],
                [TextItem(60, 100, "Détail P-1200 et F-80A")],
            ]
        ),
    )

    extraction = extract_plan(pdf, settings=PdfReportSettings())

    assert extraction.plan.pages == 3
    assert extraction.plan.references == ["EQ-40", "F-80A", "P-1200"]
    assert [warning.message for warning in extraction.warnings] == [
        "Champs introuvables : projet, numero_plan, indice, date, echelle, auteur."
    ]


def test_a_plan_without_any_text_is_reported_as_scanned(tmp_path: Path) -> None:
    pdf = write_pdf(tmp_path / "scan.pdf", PdfSpec(pages=[[], []]))

    extraction = extract_plan(pdf, settings=PdfReportSettings())

    assert extraction.plan.pages == 2 and extraction.plan.references == []
    assert [warning.message for warning in extraction.warnings] == [
        "Aucun texte trouvé : le PDF est peut-être une image scannée."
    ]

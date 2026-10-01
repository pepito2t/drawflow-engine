"""Synthetic PDF plans with a title block in the bottom-right corner."""

from pathlib import Path

from engine.testing.pdf import PdfSpec, TextItem, write_pdf

TITLE_BLOCK_X = 400


def build_report_plan(path: Path, plan_number: str, revision: str, references: list[str]) -> Path:
    body = [
        TextItem(60, 120 + index * 20, f"Voir {reference}")
        for index, reference in enumerate(references)
    ]
    title_block = [
        TextItem(TITLE_BLOCK_X, 660, "Projet : Tour B"),
        TextItem(TITLE_BLOCK_X, 680, f"N° plan : {plan_number}"),
        TextItem(TITLE_BLOCK_X, 700, f"Indice {revision}"),
        TextItem(TITLE_BLOCK_X, 720, "Date : 01.10.2026"),
        TextItem(TITLE_BLOCK_X, 740, "Échelle"),
        TextItem(TITLE_BLOCK_X, 755, "1:50"),
        TextItem(TITLE_BLOCK_X, 780, "Dessiné par TMBK"),
    ]
    return write_pdf(path, PdfSpec(pages=[body + title_block, [TextItem(60, 100, "Détail P-900")]]))

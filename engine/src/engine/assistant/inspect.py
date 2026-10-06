"""A quick look at a file handed to the assistant: what it is, and which feature fits it."""

from collections import Counter
from itertools import islice
from pathlib import Path
from typing import Any

from engine.core.cache import resolve_cache_root
from engine.core.errors import InvalidInputError
from engine.core.settings import load_general_settings

MAX_FILE_BYTES = 200_000_000
MAX_PDF_LINES = 40
MAX_TEXT_CHARS = 2_000
MAX_SHEET_ROWS = 5
MAX_SHEET_CELLS = 12
MAX_SHEETS = 5
MAX_PARAGRAPHS = 15
MAX_BLOCK_NAMES = 15
PLAN_SUFFIXES = {".dwg", ".dxf"}
SUGGESTED_FEATURE = {
    ".dwg": "dwg-parts",
    ".dxf": "dwg-parts",
    ".pdf": "pdf-report",
    ".xlsx": "soumission",
}


def inspect_file(settings: Path, raw_path: str) -> dict[str, Any]:
    path = Path(raw_path)
    if not path.is_absolute() or not path.is_file():
        raise InvalidInputError("Fichier introuvable.", file=path, hint="Donne le chemin complet.")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise InvalidInputError("Fichier trop volumineux pour être inspecté.", file=path)
    suffix = path.suffix.lower()
    base = {
        "file": str(path),
        "name": path.name,
        "type": suffix.lstrip("."),
        "size_bytes": path.stat().st_size,
        "suggested_feature": SUGGESTED_FEATURE.get(suffix),
    }
    if suffix in PLAN_SUFFIXES:
        return {**base, **_plan(path, settings)}
    if suffix == ".pdf":
        return {**base, **_pdf(path)}
    if suffix == ".xlsx":
        return {**base, **_workbook(path)}
    if suffix == ".docx":
        return {**base, **_document(path)}
    raise InvalidInputError(
        "Type de fichier non pris en charge.",
        file=path,
        hint="Drawflow lit les DWG, DXF, PDF, XLSX et DOCX.",
    )


def _plan(path: Path, settings: Path) -> dict[str, Any]:
    from engine.parts.oda import is_dxf, require_oda
    from engine.parts.worker import extract_file

    general = load_general_settings(settings)
    extraction = extract_file(
        path,
        oda_executable=None if is_dxf(path) else require_oda(general),
        cache_root=resolve_cache_root(general),
    )
    blocks = Counter(part.block for part in extraction.parts)
    attributes = sorted({tag for part in extraction.parts for tag in part.attributes})
    return {
        "blocks_total": sum(blocks.values()),
        "blocks": [
            {"name": name, "count": count} for name, count in blocks.most_common(MAX_BLOCK_NAMES)
        ],
        "attributes": attributes,
        "warnings": [warning.message for warning in extraction.warnings],
    }


def _pdf(path: Path) -> dict[str, Any]:
    from engine.modules.pdf_report.reader import read_pages

    pages = 0
    first_lines: list[str] = []
    for page in read_pages(path):
        pages += 1
        if page.number == 1:
            first_lines = [line.text for line in page.lines[:MAX_PDF_LINES]]
    text = "\n".join(first_lines)[:MAX_TEXT_CHARS]
    return {"pages": pages, "first_page_text": text, "scanned": pages > 0 and not text}


def _workbook(path: Path) -> dict[str, Any]:
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = []
        for sheet in workbook.worksheets[:MAX_SHEETS]:
            rows = [
                [str(cell) for cell in row[:MAX_SHEET_CELLS] if cell is not None and str(cell)]
                for row in islice(sheet.iter_rows(values_only=True), MAX_SHEET_ROWS)
            ]
            sheets.append({"sheet": sheet.title, "first_rows": [row for row in rows if row]})
    finally:
        workbook.close()
    return {"sheets": sheets}


def _document(path: Path) -> dict[str, Any]:
    from docx import Document

    document = Document(str(path))
    paragraphs = [
        paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()
    ]
    return {
        "paragraphs": paragraphs[:MAX_PARAGRAPHS],
        "tables": len(document.tables),
    }

"""What a submission file calls its columns, and how to teach the norm these names."""

from io import BytesIO
from pathlib import Path
from typing import IO, Any

from engine.core.errors import InvalidInputError
from engine.core.fields import KeyValue
from engine.core.registry import discover_modules
from engine.core.settings import load_section, read_document, save_settings
from engine.core.text import fold
from engine.modules.soumission.attachments import embedded_workbooks
from engine.modules.soumission.messages import t
from engine.modules.soumission.reader import header_candidates, match_columns, open_workbook
from engine.modules.soumission.settings import (
    SYNONYM_SEPARATOR,
    SoumissionSettings,
    synonyms_of,
)

SECTION_ID = "soumission"
SECTION_TITLE = t("headers.section_title")
XLSX_SUFFIX = ".xlsx"
PDF_SUFFIX = ".pdf"
MAX_SHEETS = 5


def current_settings(settings_file: Path) -> SoumissionSettings:
    return load_section(SoumissionSettings, SECTION_ID, SECTION_TITLE, read_document(settings_file))


def inspect_headers(path: Path, settings: SoumissionSettings) -> dict[str, Any]:
    """Header candidates per sheet, which columns they already match, and the current norm."""
    if not path.is_file():
        raise InvalidInputError(t("headers.file_not_found"), file=path)
    suffix = path.suffix.lower()
    sources: list[tuple[str, Path | IO[bytes]]]
    if suffix == XLSX_SUFFIX:
        sources = [(path.name, path)]
    elif suffix == PDF_SUFFIX:
        sources = [(name, BytesIO(data)) for name, data in embedded_workbooks(path)]
    else:
        raise InvalidInputError(t("headers.unsupported"), file=path)
    sheets: list[dict[str, Any]] = []
    for name, stream in sources:
        workbook = open_workbook(stream, name)
        try:
            for sheet in workbook.worksheets[:MAX_SHEETS]:
                rows = list(sheet.iter_rows(values_only=True))[: settings.header_search_rows]
                candidates = header_candidates(rows)
                best = rows[candidates[0].row] if candidates else []
                sheets.append(
                    {
                        "source": name,
                        "sheet": sheet.title,
                        "candidates": [
                            {"row": candidate.row + 1, "texts": candidate.texts}
                            for candidate in candidates
                        ],
                        "recognized": _recognized(best, settings.columns),
                    }
                )
        finally:
            workbook.close()
    return {
        "file": str(path),
        "sheets": sheets,
        "columns": [
            {"key": column.key, "synonyms": synonyms_of(column)} for column in settings.columns
        ],
    }


def validate_additions(
    settings: SoumissionSettings, additions: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Only existing columns, only non-empty new names; the result is what will be saved."""
    known = {column.key: synonyms_of(column) for column in settings.columns}
    cleaned: dict[str, list[str]] = {}
    for column, synonyms in additions.items():
        if column not in known:
            available = ", ".join(known)
            raise InvalidInputError(
                t("headers.unknown_column", column=column),
                hint=t("headers.unknown_column.hint", available=available),
            )
        existing = {fold(synonym) for synonym in known[column]}
        fresh = [
            synonym.strip()
            for synonym in synonyms
            if synonym.strip() and fold(synonym) not in existing
        ]
        if fresh:
            cleaned[column] = list(dict.fromkeys(fresh))
    if not cleaned:
        raise InvalidInputError(t("headers.nothing_to_add"))
    return cleaned


def add_synonyms(settings_file: Path, additions: dict[str, list[str]]) -> dict[str, Any]:
    settings = current_settings(settings_file)
    cleaned = validate_additions(settings, additions)
    columns = [
        KeyValue(
            key=column.key,
            value=SYNONYM_SEPARATOR.join([*synonyms_of(column), *cleaned.get(column.key, [])]),
        )
        for column in settings.columns
    ]
    section = {**settings.model_dump(mode="json"), "columns": [c.model_dump() for c in columns]}
    save_settings(settings_file, {SECTION_ID: section}, discover_modules())
    return {"added": cleaned}


def _recognized(row: Any, columns: list[KeyValue]) -> dict[str, str]:
    positions = match_columns(row, columns)
    return {column: str(row[position]) for column, position in positions.items()}

from collections.abc import Sequence
from pathlib import Path

from engine.core.xlsx import CellValue, fit_columns, open_sheet, save_workbook, write_row
from engine.modules.soumission.reader import SubmissionTable

SOURCE_HEADER = "Fichier source"
SHEET_HEADER = "Feuille"
HEADER_ROW = 1


def export_submissions(
    tables: Sequence[SubmissionTable], columns: Sequence[str], target: Path
) -> int:
    """Writes every normalized row in one sheet and returns the row count."""
    workbook, sheet = open_sheet(None, None)
    header: list[CellValue] = [*columns, SOURCE_HEADER, SHEET_HEADER]
    rows = [
        [*(row.get(column, "") for column in columns), table.source, table.sheet]
        for table in tables
        for row in table.rows
    ]
    write_row(sheet, HEADER_ROW, header, bold=True)
    for offset, row in enumerate(rows, start=1):
        write_row(sheet, HEADER_ROW + offset, row)
    sheet.freeze_panes = f"A{HEADER_ROW + 1}"
    fit_columns(sheet, [header, *rows])
    save_workbook(workbook, target)
    return len(rows)

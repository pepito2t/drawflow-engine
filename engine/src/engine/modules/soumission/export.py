from collections.abc import Sequence
from pathlib import Path

from engine.core.xlsx import CellValue, open_sheet, save_workbook, write_table
from engine.modules.soumission.messages import t
from engine.modules.soumission.reader import SubmissionTable

SOURCE_HEADER = t("export.source_header")
SHEET_HEADER = t("export.sheet_header")


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
    write_table(sheet, header, rows)
    save_workbook(workbook, target)
    return len(rows)

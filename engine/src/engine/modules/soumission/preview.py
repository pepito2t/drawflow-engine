"""The normalized table as it would be exported, amounts kept as text pointed out."""

from collections.abc import Collection, Sequence

from engine.core.events import TableEvent, TableRow
from engine.modules.soumission.export import SHEET_HEADER, SOURCE_HEADER
from engine.modules.soumission.reader import SubmissionTable

PREVIEW_MAX_ROWS = 500
TEXT_AMOUNT_ISSUE = "Montant illisible : colonne « {column} »"


def preview_table(
    tables: Sequence[SubmissionTable], columns: Sequence[str], numeric: Collection[str]
) -> TableEvent:
    numeric_columns = set(numeric)
    rows: list[TableRow] = []
    total = 0
    for table in tables:
        for row in table.rows:
            total += 1
            if len(rows) >= PREVIEW_MAX_ROWS:
                continue
            cells = [str(row.get(column, "")) for column in columns]
            issues = [
                TEXT_AMOUNT_ISSUE.format(column=column)
                for column in columns
                if column in numeric_columns and isinstance(row.get(column), str) and row[column]
            ]
            rows.append(TableRow(cells=[*cells, table.source, table.sheet], issues=issues))
    headers = [*columns, SOURCE_HEADER, SHEET_HEADER]
    return TableEvent(headers=headers, rows=rows, total=total)

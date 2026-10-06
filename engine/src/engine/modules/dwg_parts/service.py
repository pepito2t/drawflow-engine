from engine.core.events import TableEvent, TableRow
from engine.parts.listing import PartsList

DOCUMENT_TYPE = "liste-pieces"
QUANTITY_HEADER = "Quantité"
SOURCES_HEADER = "Plans"
PREVIEW_MAX_ROWS = 500
EMPTY_CELL_ISSUE = "Colonne « {column} » vide"


def preview_table(parts_list: PartsList) -> TableEvent:
    """What the Excel file would contain, with every empty cell pointed out."""
    rows = [
        TableRow(
            cells=[*line.values, _quantity_text(line.quantity), ", ".join(line.sources)],
            issues=[
                EMPTY_CELL_ISSUE.format(column=column)
                for column, value in zip(parts_list.headers, line.values, strict=True)
                if not value.strip()
            ],
        )
        for line in parts_list.lines[:PREVIEW_MAX_ROWS]
    ]
    headers = [*parts_list.headers, QUANTITY_HEADER, SOURCES_HEADER]
    return TableEvent(headers=headers, rows=rows, total=len(parts_list.lines))


def _quantity_text(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(round(value, 2))


def describe_result(parts_list: PartsList, read: int, total: int) -> str:
    quantity = parts_list.total_quantity
    pieces = int(quantity) if float(quantity).is_integer() else round(quantity, 2)
    return f"{len(parts_list.lines)} ligne(s), {pieces} pièce(s), {read}/{total} plan(s) lu(s)"

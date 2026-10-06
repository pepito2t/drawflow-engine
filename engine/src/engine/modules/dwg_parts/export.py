from collections.abc import Sequence
from pathlib import Path

from engine.core.xlsx import CellValue, fit_columns, open_sheet, save_workbook, write_row
from engine.parts.aggregation import PartLine
from engine.parts.settings import PartsListSettings

QUANTITY_HEADER = "Quantité"
SOURCES_HEADER = "Plans"
SOURCES_SEPARATOR = ", "


def export_parts(
    lines: Sequence[PartLine],
    headers: Sequence[str],
    target: Path,
    template: Path | None,
    settings: PartsListSettings,
) -> None:
    workbook, sheet = open_sheet(template, settings.template_sheet or None)
    header = [*headers, QUANTITY_HEADER, SOURCES_HEADER]
    rows = [_row(line) for line in lines]
    write_row(sheet, settings.header_row, header, bold=True)
    for offset, row in enumerate(rows, start=1):
        write_row(sheet, settings.header_row + offset, row)
    if template is None:
        sheet.freeze_panes = f"A{settings.header_row + 1}"
        fit_columns(sheet, [header, *rows])
    save_workbook(workbook, target)


def _row(line: PartLine) -> list[CellValue]:
    return [*line.values, _quantity(line.quantity), SOURCES_SEPARATOR.join(line.sources)]


def _quantity(value: float) -> CellValue:
    return int(value) if value.is_integer() else value

from collections.abc import Sequence
from pathlib import Path

from openpyxl.worksheet.worksheet import Worksheet

from engine.core.xlsx import CellValue, open_sheet, quantity_cell, save_workbook, write_table
from engine.modules.dwg_parts.messages import t
from engine.parts.aggregation import PartLine
from engine.parts.settings import PartsListSettings

QUANTITY_HEADER = t("export.quantity_header")
SOURCES_HEADER = t("export.sources_header")
SOURCES_SEPARATOR = ", "


TOTAL_SHEET = t("export.total_sheet")


def export_parts(
    lines: Sequence[PartLine],
    headers: Sequence[str],
    target: Path,
    template: Path | None,
    settings: PartsListSettings,
    total: tuple[Sequence[str], Sequence[PartLine]] | None = None,
) -> None:
    workbook, sheet = open_sheet(template, settings.template_sheet or None)
    _write_sheet(sheet, headers, lines, settings.header_row, fit=template is None)
    if total is not None:
        total_headers, total_lines = total
        _write_sheet(workbook.create_sheet(TOTAL_SHEET), total_headers, total_lines, 1, fit=True)
    save_workbook(workbook, target)


def _write_sheet(
    sheet: Worksheet,
    headers: Sequence[str],
    lines: Sequence[PartLine],
    header_row: int,
    *,
    fit: bool,
) -> None:
    header = [*headers, QUANTITY_HEADER, SOURCES_HEADER]
    rows = [_row(line) for line in lines]
    write_table(sheet, header, rows, header_row=header_row, fit=fit)


def _row(line: PartLine) -> list[CellValue]:
    return [*line.values, quantity_cell(line.quantity), SOURCES_SEPARATOR.join(line.sources)]

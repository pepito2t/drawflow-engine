from collections.abc import Sequence
from pathlib import Path

from engine.core.xlsx import CellValue, fit_columns, open_sheet, save_workbook, write_row
from engine.modules.dwg_diff.service import (
    DELTA_HEADER,
    PLANS_AFTER_HEADER,
    PLANS_BEFORE_HEADER,
    QUANTITY_AFTER_HEADER,
    QUANTITY_BEFORE_HEADER,
    DiffLine,
    DiffReport,
    PlanStatus,
    join_plans,
)

SHEETS = (
    ("Ajouts", "added"),
    ("Suppressions", "removed"),
    ("Modifications", "changed"),
    ("Inchangés", "unchanged"),
)
PLANS_SHEET = "Plans"
PLAN_HEADERS = ("Plan", "Indice A", "Indice B")
PRESENT, ABSENT = "oui", "non"
HEADER_ROW = 1


def export_diff(report: DiffReport, target: Path) -> None:
    """One sheet per category, then the plans of each index side by side."""
    workbook, first = open_sheet(None, None)
    first.title = SHEETS[0][0]
    for index, (title, attribute) in enumerate(SHEETS):
        sheet = first if index == 0 else workbook.create_sheet(title)
        lines: Sequence[DiffLine] = getattr(report, attribute)
        rows = [_row(line) for line in lines]
        _write(sheet, _headers(report), rows)
    plans_sheet = workbook.create_sheet(PLANS_SHEET)
    _write(plans_sheet, PLAN_HEADERS, [_plan_row(plan) for plan in report.plans])
    save_workbook(workbook, target)


def _headers(report: DiffReport) -> list[CellValue]:
    return [
        *report.headers,
        QUANTITY_BEFORE_HEADER,
        QUANTITY_AFTER_HEADER,
        DELTA_HEADER,
        PLANS_BEFORE_HEADER,
        PLANS_AFTER_HEADER,
    ]


def _row(line: DiffLine) -> list[CellValue]:
    return [
        *line.values,
        _quantity(line.before),
        _quantity(line.after),
        _quantity(line.delta),
        join_plans(line.plans_before),
        join_plans(line.plans_after),
    ]


def _plan_row(plan: PlanStatus) -> list[CellValue]:
    return [plan.name, PRESENT if plan.in_before else ABSENT, PRESENT if plan.in_after else ABSENT]


def _quantity(value: float) -> CellValue:
    return int(value) if value.is_integer() else value


def _write(
    sheet: object, headers: Sequence[CellValue], rows: Sequence[Sequence[CellValue]]
) -> None:
    from openpyxl.worksheet.worksheet import Worksheet

    assert isinstance(sheet, Worksheet)
    write_row(sheet, HEADER_ROW, headers, bold=True)
    for offset, row in enumerate(rows, start=1):
        write_row(sheet, HEADER_ROW + offset, row)
    sheet.freeze_panes = f"A{HEADER_ROW + 1}"
    fit_columns(sheet, [headers, *rows])

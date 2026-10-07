from collections.abc import Sequence
from pathlib import Path

from engine.core.xlsx import CellValue, open_sheet, quantity_cell, save_workbook, write_table
from engine.modules.dwg_diff.messages import t
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
    (t("export.sheet.added"), "added"),
    (t("export.sheet.removed"), "removed"),
    (t("export.sheet.changed"), "changed"),
    (t("export.sheet.unchanged"), "unchanged"),
)
PLANS_SHEET = t("export.sheet.plans")
PLAN_HEADERS = (t("export.plan_header"), t("export.before_header"), t("export.after_header"))
PRESENT, ABSENT = t("export.present"), t("export.absent")


def export_diff(report: DiffReport, target: Path) -> None:
    """One sheet per category, then the plans of each index side by side."""
    workbook, first = open_sheet(None, None)
    first.title = SHEETS[0][0]
    for index, (title, attribute) in enumerate(SHEETS):
        sheet = first if index == 0 else workbook.create_sheet(title)
        lines: Sequence[DiffLine] = getattr(report, attribute)
        rows = [_row(line) for line in lines]
        write_table(sheet, _headers(report), rows)
    plans_sheet = workbook.create_sheet(PLANS_SHEET)
    write_table(plans_sheet, PLAN_HEADERS, [_plan_row(plan) for plan in report.plans])
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
        quantity_cell(line.before),
        quantity_cell(line.after),
        quantity_cell(line.delta),
        join_plans(line.plans_before),
        join_plans(line.plans_after),
    ]


def _plan_row(plan: PlanStatus) -> list[CellValue]:
    return [plan.name, PRESENT if plan.in_before else ABSENT, PRESENT if plan.in_after else ABSENT]

from collections.abc import Sequence
from pathlib import Path
from zipfile import BadZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.worksheet.worksheet import Worksheet

from engine.core.errors import EngineError, OutputWriteError

FORMULA_PREFIX = "="
MAX_COLUMN_WIDTH = 60
MIN_COLUMN_WIDTH = 8
COLUMN_PADDING = 2

type CellValue = str | int | float


class TemplateError(EngineError):
    pass


def open_sheet(template: Path | None, sheet_name: str | None) -> tuple[Workbook, Worksheet]:
    """Opens the user's template, or a blank workbook when none is given."""
    if template is None:
        workbook = Workbook()
        return workbook, _active_sheet(workbook)
    workbook = _load_template(template)
    if not sheet_name:
        return workbook, _active_sheet(workbook)
    if sheet_name not in workbook.sheetnames:
        available = ", ".join(workbook.sheetnames)
        raise TemplateError(
            f"La feuille « {sheet_name} » n'existe pas dans le modèle.",
            file=template,
            hint=f"Feuilles disponibles : {available}. Corrigez le nom dans Paramètres.",
        )
    return workbook, workbook[sheet_name]


def write_row(
    sheet: Worksheet, row: int, values: Sequence[CellValue], *, bold: bool = False
) -> None:
    for column, value in enumerate(values, start=1):
        cell = sheet.cell(row=row, column=column, value=value)
        _keep_text_literal(cell, value)
        if bold:
            cell.font = Font(bold=True)


def fit_columns(sheet: Worksheet, rows: Sequence[Sequence[CellValue]]) -> None:
    for column in range(1, max((len(row) for row in rows), default=0) + 1):
        longest = max((len(str(row[column - 1])) for row in rows if len(row) >= column), default=0)
        width = min(max(longest + COLUMN_PADDING, MIN_COLUMN_WIDTH), MAX_COLUMN_WIDTH)
        sheet.column_dimensions[get_column_letter(column)].width = width


def save_workbook(workbook: Workbook, target: Path) -> None:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(target)
    except OSError as error:
        raise OutputWriteError(
            "Impossible d'enregistrer le classeur.",
            file=target,
            hint="Fermez le fichier s'il est ouvert dans Excel et vérifiez le dossier de sortie.",
        ) from error


def _keep_text_literal(cell: Cell, value: CellValue) -> None:
    # Attribute text starting with "=" must never be evaluated as a formula.
    if isinstance(value, str) and value.startswith(FORMULA_PREFIX):
        cell.data_type = "s"


def _load_template(template: Path) -> Workbook:
    try:
        return load_workbook(template)
    except (OSError, BadZipFile, InvalidFileException, KeyError) as error:
        raise TemplateError(
            "Le modèle Excel est illisible.",
            file=template,
            hint="Choisissez un fichier .xlsx valide (pas .xls ni .xlsm).",
        ) from error


def _active_sheet(workbook: Workbook) -> Worksheet:
    sheet = workbook.active
    if not isinstance(sheet, Worksheet):
        raise TemplateError("Le modèle Excel ne contient pas de feuille de calcul.")
    return sheet

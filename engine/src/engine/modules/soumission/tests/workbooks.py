"""Synthetic submission workbooks used by tests and the frozen-binary smoke test."""

import zipfile
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet


def submission_bytes(title_rows: int = 2) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    assert isinstance(sheet, Worksheet)
    sheet.title = "Offre"
    for index in range(title_rows):
        sheet.append([f"Entreprise Façades SA — ligne {index + 1}"])
    sheet.append(["Pos.", "Désignation", "Qté", "Unité", "P.U.", "Montant"])
    sheet.append(["1.1", "Panneau composite RAL 7016", "12", "m2", "1'234.50", None])
    sheet.append([None, None, None, None, None, None])
    sheet.append(["1.2", "Équerre alu", 40, "pce", 3.5, 140])
    sheet.append(["1.3", "Montage", "forfait", "gl", "CHF 2'000.-", "2 000,00"])
    workbook.create_sheet("Notes").append(["Rien à voir ici"])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def write_submission(path: Path) -> Path:
    path.write_bytes(submission_bytes())
    return path


def truncated_sheet_bytes() -> bytes:
    """A workbook that opens, whose first sheet's XML stops halfway: Excel reports it damaged."""
    source = BytesIO(submission_bytes())
    target = BytesIO()
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(target, "w") as damaged:
        for item in original.infolist():
            content = original.read(item)
            if item.filename == "xl/worksheets/sheet1.xml":
                content = content[: len(content) // 2]
            damaged.writestr(item, content)
    return target.getvalue()

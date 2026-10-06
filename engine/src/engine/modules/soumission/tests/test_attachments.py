from pathlib import Path

import pytest

from engine.modules.soumission.attachments import (
    NO_WORKBOOK_WARNING,
    PdfAttachmentError,
    read_pdf_submission,
)
from engine.modules.soumission.settings import SoumissionSettings
from engine.modules.soumission.tests.workbooks import submission_bytes
from engine.testing.pdf import PdfSpec, TextItem, write_pdf


def test_reads_every_embedded_workbook(tmp_path: Path) -> None:
    spec = PdfSpec(
        pages=[[TextItem(50, 50, "Soumission")]],
        attachments={
            "lot-1.xlsx": submission_bytes(),
            "lot-2.XLSX": submission_bytes(),
            "notes.txt": b"x",
        },
    )
    path = write_pdf(tmp_path / "soumission é.pdf", spec)

    content = read_pdf_submission(path, SoumissionSettings())

    assert [table.source for table in content.tables] == [
        "soumission é.pdf > lot-1.xlsx",
        "soumission é.pdf > lot-2.XLSX",
    ]
    assert content.tables[0].rows[0]["Position"] == "1.1"
    assert content.warnings[0].location is not None
    assert content.warnings[0].location.startswith("lot-1.xlsx")


def test_pdf_without_workbook_is_flagged(tmp_path: Path) -> None:
    path = write_pdf(tmp_path / "vide.pdf", PdfSpec(pages=[[]]))

    content = read_pdf_submission(path, SoumissionSettings())

    assert content.tables == []
    assert [warning.message for warning in content.warnings] == [NO_WORKBOOK_WARNING]
    assert content.warnings[0].hint is not None


def test_damaged_pdf_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "cassé.pdf"
    path.write_bytes(b"pas un pdf")

    with pytest.raises(PdfAttachmentError) as caught:
        read_pdf_submission(path, SoumissionSettings())

    assert caught.value.file == path

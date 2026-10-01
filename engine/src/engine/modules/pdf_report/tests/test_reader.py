from pathlib import Path

import pytest

from engine.modules.pdf_report.reader import PdfReadError, read_pages
from engine.testing.pdf import PdfSpec, TextItem, write_pdf


def test_reads_lines_page_by_page_with_positions(tmp_path: Path) -> None:
    spec = PdfSpec(
        pages=[
            [TextItem(50, 100, "Projet : Tour B"), TextItem(50, 120, "Façade nord")],
            [TextItem(400, 800, "Indice C")],
        ]
    )
    path = write_pdf(tmp_path / "plans é.pdf", spec)

    pages = list(read_pages(path))

    assert [page.number for page in pages] == [1, 2]
    assert [line.text for line in pages[0].lines] == ["Projet : Tour B", "Façade nord"]
    assert pages[1].lines[0].x0 == pytest.approx(400, abs=1)
    assert pages[1].lines[0].top > 780


def test_words_on_the_same_row_form_one_line(tmp_path: Path) -> None:
    spec = PdfSpec(pages=[[TextItem(300, 50, "Échelle"), TextItem(50, 50, "Plan")]])

    [page] = read_pages(write_pdf(tmp_path / "p.pdf", spec))

    assert [line.text for line in page.lines] == ["Plan Échelle"]


def test_page_without_text_has_no_lines(tmp_path: Path) -> None:
    [page] = read_pages(write_pdf(tmp_path / "scan.pdf", PdfSpec(pages=[[]])))

    assert page.lines == []


def test_damaged_pdf_is_reported(tmp_path: Path) -> None:
    broken = tmp_path / "cassé.pdf"
    broken.write_bytes(b"%PDF-1.7\nnot really")

    with pytest.raises(PdfReadError) as caught:
        list(read_pages(broken))

    assert caught.value.file == broken
    assert caught.value.hint is not None

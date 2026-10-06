from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError
from pdfplumber.utils.exceptions import PdfminerException

from engine.core.errors import EngineError
from engine.modules.pdf_report.messages import t

LINE_TOLERANCE_POINTS = 3
WORD_SEPARATOR = " "


class PdfReadError(EngineError):
    pass


@dataclass(frozen=True)
class TextLine:
    text: str
    x0: float
    top: float
    x1: float
    bottom: float


@dataclass(frozen=True)
class PageText:
    number: int
    width: float
    height: float
    lines: list[TextLine]


def read_pages(path: Path) -> Iterator[PageText]:
    """Yields one page at a time so large plan sets never sit in memory together."""
    try:
        with pdfplumber.open(path) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                words = page.extract_words(use_text_flow=True)
                yield PageText(number, float(page.width), float(page.height), _group_lines(words))
                page.close()
    except (PdfminerException, PDFSyntaxError, PDFPasswordIncorrect) as error:
        raise _readable_error(path, error) from error
    except OSError as error:
        raise PdfReadError(t("reader.inaccessible"), file=path) from error


def _group_lines(words: list[dict[str, object]]) -> list[TextLine]:
    rows: dict[int, list[dict[str, object]]] = {}
    for word in words:
        key = round(_number(word, "top") / LINE_TOLERANCE_POINTS)
        rows.setdefault(key, []).append(word)
    lines = [_merge(sorted(row, key=lambda word: _number(word, "x0"))) for row in rows.values()]
    return sorted(lines, key=lambda line: (line.top, line.x0))


def _merge(words: list[dict[str, object]]) -> TextLine:
    return TextLine(
        text=WORD_SEPARATOR.join(str(word["text"]) for word in words),
        x0=min(_number(word, "x0") for word in words),
        top=min(_number(word, "top") for word in words),
        x1=max(_number(word, "x1") for word in words),
        bottom=max(_number(word, "bottom") for word in words),
    )


def _number(word: dict[str, object], key: str) -> float:
    value = word[key]
    return float(value) if isinstance(value, int | float) else 0.0


def _readable_error(path: Path, error: Exception) -> PdfReadError:
    cause = error.args[0] if isinstance(error, PdfminerException) and error.args else error
    if isinstance(cause, PDFPasswordIncorrect):
        return PdfReadError(t("reader.protected"), file=path, hint=t("reader.protected.hint"))
    return PdfReadError(t("reader.unreadable"), file=path, hint=t("reader.unreadable.hint"))

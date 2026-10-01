from engine.modules.pdf_report.reader import PageText, TextLine
from engine.modules.pdf_report.settings import PdfReportSettings
from engine.modules.pdf_report.zone import Zone, lines_in_zone


def line(text: str, x: float, y: float) -> TextLine:
    return TextLine(text=text, x0=x, top=y, x1=x + 10, bottom=y + 10)


PAGE = PageText(
    number=1,
    width=1000,
    height=1000,
    lines=[
        line("Note générale", 100, 100),
        line("Projet : Tour B", 700, 850),
        line("Indice C", 900, 950),
    ],
)


def test_default_zone_is_the_bottom_right_corner() -> None:
    zone = Zone.title_block(PdfReportSettings())

    assert [found.text for found in lines_in_zone(PAGE, zone)] == ["Projet : Tour B", "Indice C"]


def test_zone_is_configurable() -> None:
    zone = Zone.title_block(
        PdfReportSettings(
            title_block_left=0, title_block_top=0, title_block_right=20, title_block_bottom=20
        )
    )

    assert [found.text for found in lines_in_zone(PAGE, zone)] == ["Note générale"]

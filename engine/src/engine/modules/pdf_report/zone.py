from dataclasses import dataclass

from engine.modules.pdf_report.reader import PageText, TextLine
from engine.modules.pdf_report.settings import PdfReportSettings

PERCENT = 100


@dataclass(frozen=True)
class Zone:
    left: float
    top: float
    right: float
    bottom: float

    @classmethod
    def title_block(cls, settings: PdfReportSettings) -> "Zone":
        return cls(
            settings.title_block_left / PERCENT,
            settings.title_block_top / PERCENT,
            settings.title_block_right / PERCENT,
            settings.title_block_bottom / PERCENT,
        )


def lines_in_zone(page: PageText, zone: Zone) -> list[TextLine]:
    """Keeps lines whose centre falls inside the zone, expressed as page fractions."""
    return [line for line in page.lines if _contains(page, zone, line)]


def _contains(page: PageText, zone: Zone, line: TextLine) -> bool:
    centre_x = (line.x0 + line.x1) / 2 / page.width
    centre_y = (line.top + line.bottom) / 2 / page.height
    return zone.left <= centre_x <= zone.right and zone.top <= centre_y <= zone.bottom

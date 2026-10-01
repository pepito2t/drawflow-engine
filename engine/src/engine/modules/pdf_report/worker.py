from dataclasses import dataclass, field
from pathlib import Path

from engine.modules.pdf_report.fields import extract_fields, find_references
from engine.modules.pdf_report.reader import TextLine, read_pages
from engine.modules.pdf_report.report import PlanData
from engine.modules.pdf_report.settings import PdfReportSettings
from engine.modules.pdf_report.zone import Zone, lines_in_zone

NO_TEXT_WARNING = "Aucun texte trouvé : le PDF est peut-être une image scannée."


@dataclass(frozen=True)
class PlanExtraction:
    plan: PlanData
    warnings: list[str] = field(default_factory=list)


def extract_plan(path: Path, *, settings: PdfReportSettings) -> PlanExtraction:
    """Runs in a worker process; reads the PDF one page at a time."""
    zone = Zone.title_block(settings)
    title_block: list[TextLine] = []
    all_lines: list[TextLine] = []
    pages = 0
    for page in read_pages(path):
        pages += 1
        title_block.extend(lines_in_zone(page, zone))
        all_lines.extend(page.lines)
    fields = extract_fields(title_block, settings.fields)
    plan = PlanData(
        file_name=path.name,
        pages=pages,
        fields=fields.values,
        references=find_references(all_lines, settings.reference_pattern),
    )
    return PlanExtraction(plan=plan, warnings=_warnings(all_lines, fields.missing))


def _warnings(lines: list[TextLine], missing: list[str]) -> list[str]:
    if not lines:
        return [NO_TEXT_WARNING]
    if missing:
        return [f"Champs introuvables dans le cartouche : {', '.join(missing)}."]
    return []

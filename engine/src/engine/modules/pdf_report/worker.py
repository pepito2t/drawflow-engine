from dataclasses import dataclass, field
from pathlib import Path

from engine.core.anomalies import Anomaly
from engine.modules.pdf_report.fields import extract_fields, find_references
from engine.modules.pdf_report.messages import t
from engine.modules.pdf_report.reader import TextLine, read_pages
from engine.modules.pdf_report.report import PlanData
from engine.modules.pdf_report.settings import PdfReportSettings
from engine.modules.pdf_report.zone import Zone, lines_in_zone

MISSING_FIELDS_SEPARATOR = ", "


@dataclass(frozen=True)
class PlanExtraction:
    plan: PlanData
    warnings: list[Anomaly] = field(default_factory=list)


def extract_plan(path: Path, *, settings: PdfReportSettings) -> PlanExtraction:
    """Runs in a worker process; reads the PDF one page at a time."""
    zone = Zone.title_block(settings)
    title_block: list[TextLine] = []
    references: set[str] = set()
    pages = 0
    has_text = False
    for page in read_pages(path):
        pages += 1
        has_text = has_text or bool(page.lines)
        title_block.extend(lines_in_zone(page, zone))
        references.update(find_references(page.lines, settings.reference_pattern))
    fields = extract_fields(title_block, settings.fields)
    plan = PlanData(
        file_name=path.name, pages=pages, fields=fields.values, references=sorted(references)
    )
    return PlanExtraction(plan=plan, warnings=_warnings(has_text, fields.missing))


def _warnings(has_text: bool, missing: list[str]) -> list[Anomaly]:
    if not has_text:
        return [Anomaly(t("worker.no_text"), hint=t("worker.no_text.hint"))]
    if missing:
        return [
            Anomaly(
                t("worker.missing_fields", fields=MISSING_FIELDS_SEPARATOR.join(missing)),
                location=t("worker.missing_fields.location"),
                hint=t("worker.missing_fields.hint"),
            )
        ]
    return []

from pathlib import Path

from engine.modules.soumission.attachments import read_pdf_submission
from engine.modules.soumission.reader import WorkbookContent, read_workbook
from engine.modules.soumission.settings import SoumissionSettings

PDF_SUFFIX = ".pdf"


def read_submission(path: Path, *, settings: SoumissionSettings) -> WorkbookContent:
    """Runs in a worker process; PDFs are read through their embedded workbooks."""
    if path.suffix.lower() == PDF_SUFFIX:
        return read_pdf_submission(path, settings)
    return read_workbook(path, path.name, settings)

from dataclasses import dataclass
from pathlib import Path

from engine.core.cache import file_digest
from engine.core.errors import EngineError
from engine.modules.soumission.attachments import read_pdf_submission
from engine.modules.soumission.messages import t
from engine.modules.soumission.reader import WorkbookContent, read_workbook
from engine.modules.soumission.settings import SoumissionSettings

PDF_SUFFIX = ".pdf"


class SourceReadError(EngineError):
    pass


@dataclass(frozen=True)
class SubmissionRead:
    digest: str
    content: WorkbookContent


def read_submission(path: Path, *, settings: SoumissionSettings) -> SubmissionRead:
    """Runs in a worker process; the digest lets identical copies be told apart after the batch."""
    try:
        digest = file_digest(path)
    except OSError as error:
        raise SourceReadError(
            t("worker.unreadable_source"), file=path, hint=t("worker.unreadable_source.hint")
        ) from error
    if path.suffix.lower() == PDF_SUFFIX:
        return SubmissionRead(digest, read_pdf_submission(path, settings))
    return SubmissionRead(digest, read_workbook(path, path.name, settings))

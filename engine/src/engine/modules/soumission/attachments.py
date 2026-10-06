from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

from engine.core.anomalies import Anomaly
from engine.core.errors import EngineError
from engine.modules.soumission.messages import t
from engine.modules.soumission.reader import SubmissionTable, WorkbookContent, read_workbook
from engine.modules.soumission.settings import SoumissionSettings

XLSX_SUFFIX = ".xlsx"
SOURCE_SEPARATOR = " > "
NO_WORKBOOK_WARNING = t("attachments.no_workbook")


class PdfAttachmentError(EngineError):
    pass


def read_pdf_submission(path: Path, settings: SoumissionSettings) -> WorkbookContent:
    """Reads every .xlsx embedded in the PDF as if it were a standalone workbook."""
    tables: list[SubmissionTable] = []
    warnings: list[Anomaly] = []
    workbooks = embedded_workbooks(path)
    for name, data in workbooks:
        content = read_workbook(BytesIO(data), f"{path.name}{SOURCE_SEPARATOR}{name}", settings)
        tables.extend(content.tables)
        warnings.extend(warning.within(name) for warning in content.warnings)
    if not workbooks:
        warnings.append(Anomaly(NO_WORKBOOK_WARNING, hint=t("attachments.no_workbook.hint")))
    return WorkbookContent(tables=tables, warnings=warnings)


def embedded_workbooks(path: Path) -> list[tuple[str, bytes]]:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise _protected(path)
        return [
            (name, data)
            for name, contents in reader.attachments.items()
            if name.lower().endswith(XLSX_SUFFIX)
            for data in contents
        ]
    except FileNotDecryptedError as error:
        raise _protected(path) from error
    except (PdfReadError, OSError) as error:
        raise PdfAttachmentError(
            t("attachments.unreadable"), file=path, hint=t("attachments.unreadable.hint")
        ) from error


def _protected(path: Path) -> PdfAttachmentError:
    return PdfAttachmentError(
        t("attachments.protected"), file=path, hint=t("attachments.protected.hint")
    )

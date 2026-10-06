from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

from engine.core.anomalies import Anomaly
from engine.core.errors import EngineError
from engine.modules.soumission.reader import SubmissionTable, WorkbookContent, read_workbook
from engine.modules.soumission.settings import SoumissionSettings

XLSX_SUFFIX = ".xlsx"
SOURCE_SEPARATOR = " > "
NO_WORKBOOK_WARNING = "Aucun classeur Excel joint à ce PDF."


class PdfAttachmentError(EngineError):
    pass


def read_pdf_submission(path: Path, settings: SoumissionSettings) -> WorkbookContent:
    """Reads every .xlsx embedded in the PDF as if it were a standalone workbook."""
    tables: list[SubmissionTable] = []
    warnings: list[Anomaly] = []
    workbooks = _embedded_workbooks(path)
    for name, data in workbooks:
        content = read_workbook(BytesIO(data), f"{path.name}{SOURCE_SEPARATOR}{name}", settings)
        tables.extend(content.tables)
        warnings.extend(warning.within(name) for warning in content.warnings)
    if not workbooks:
        warnings.append(
            Anomaly(
                NO_WORKBOOK_WARNING,
                hint="Traitez le classeur Excel directement, ou demandez un PDF avec le "
                "classeur joint.",
            )
        )
    return WorkbookContent(tables=tables, warnings=warnings)


def _embedded_workbooks(path: Path) -> list[tuple[str, bytes]]:
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
            "Le PDF est illisible ou endommagé.",
            file=path,
            hint="Ré-exportez la soumission en PDF depuis le logiciel d'origine.",
        ) from error


def _protected(path: Path) -> PdfAttachmentError:
    return PdfAttachmentError(
        "Le PDF est protégé par un mot de passe.",
        file=path,
        hint="Enregistrez une copie sans protection puis relancez.",
    )

from datetime import datetime
from functools import partial
from pathlib import Path

from engine.core.anomalies import emit_anomalies
from engine.core.batch import process_batch
from engine.core.collect import collect_files
from engine.core.contract import ModuleResult, RunContext
from engine.core.errors import EngineError
from engine.core.events import LogEvent, WarningEvent
from engine.core.naming import naming_values, output_target, writing_output
from engine.modules.soumission.dedupe import deduplicate
from engine.modules.soumission.export import export_submissions
from engine.modules.soumission.preview import preview_table
from engine.modules.soumission.reader import SubmissionTable, WorkbookContent
from engine.modules.soumission.schema import SoumissionInputs
from engine.modules.soumission.settings import SoumissionSettings
from engine.modules.soumission.worker import read_submission

SOURCE_SUFFIXES = frozenset({".xlsx", ".pdf"})
SOURCE_KIND = "XLSX ou PDF"
DOCUMENT_TYPE = "soumission"
OUTPUT_EXTENSION = "xlsx"
READ_LABEL = "Lecture"


def run_soumission(inputs: SoumissionInputs, context: RunContext, moment: datetime) -> ModuleResult:
    settings = context.settings_as(SoumissionSettings)
    collected = collect_files(
        inputs.files,
        inputs.folders,
        suffixes=SOURCE_SUFFIXES,
        kind=SOURCE_KIND,
        recursive=inputs.recursive,
        emit=context.emit,
    )
    sources = _without_duplicates(collected, context)
    outcome = process_batch(
        sources,
        partial(read_submission, settings=settings),
        batch_size=context.general.batch_size,
        emit=context.emit,
        label=READ_LABEL,
    )
    tables = _tables(outcome.results, context)
    if not tables:
        raise EngineError(
            "Aucun tableau de soumission n'a été reconnu.",
            hint="Vérifiez les en-têtes reconnus dans Paramètres → Soumission.",
        )
    columns = [column.key for column in settings.columns]
    context.emit(preview_table(tables, columns, settings.numeric_column_names()))
    if inputs.preview:
        count = sum(len(table.rows) for table in tables)
        return ModuleResult(
            summary=f"Aperçu : {count} ligne(s) issues de {len(tables)} tableau(x)", preview=True
        )
    target = _target(inputs, settings, moment)
    context.emit(LogEvent(message=f"Écriture de {target.name}"))
    with writing_output(target):
        count = export_submissions(tables, columns, target)
    summary = f"{count} ligne(s) issues de {len(tables)} tableau(x), {len(sources)} fichier(s)"
    return ModuleResult(summary=summary, outputs=[target])


def _without_duplicates(paths: list[Path], context: RunContext) -> list[Path]:
    result = deduplicate(paths)
    for duplicate in result.duplicates:
        message = f"Doublon ignoré : même contenu que {duplicate.same_as.name}."
        context.emit(WarningEvent(message=message, file=str(duplicate.path)))
    return result.unique


def _tables(
    results: list[tuple[Path, WorkbookContent]], context: RunContext
) -> list[SubmissionTable]:
    tables: list[SubmissionTable] = []
    for path, content in results:
        emit_anomalies(context.emit, content.warnings, path)
        tables.extend(content.tables)
    return tables


def _target(inputs: SoumissionInputs, settings: SoumissionSettings, moment: datetime) -> Path:
    values = naming_values(moment, projet=inputs.project.strip(), type=DOCUMENT_TYPE)
    return output_target(
        inputs.output_folder, settings.file_name_template, values, OUTPUT_EXTENSION
    )

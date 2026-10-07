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
from engine.modules.soumission.messages import t
from engine.modules.soumission.preview import preview_table
from engine.modules.soumission.reader import SubmissionTable, WorkbookContent
from engine.modules.soumission.schema import SoumissionInputs
from engine.modules.soumission.settings import SoumissionSettings
from engine.modules.soumission.worker import read_submission

SOURCE_SUFFIXES = frozenset({".xlsx", ".pdf"})
DOCUMENT_TYPE = "soumission"
OUTPUT_EXTENSION = "xlsx"


def run_soumission(inputs: SoumissionInputs, context: RunContext, moment: datetime) -> ModuleResult:
    settings = context.settings_as(SoumissionSettings)
    collected = collect_files(
        inputs.files,
        inputs.folders,
        suffixes=SOURCE_SUFFIXES,
        kind=t("pipeline.source_kind"),
        recursive=inputs.recursive,
        emit=context.emit,
    )
    sources = _without_duplicates(collected, context)
    outcome = process_batch(
        sources,
        partial(read_submission, settings=settings),
        batch_size=context.general.batch_size,
        emit=context.emit,
        label=t("pipeline.read_label"),
        settings_file=context.settings_file,
    )
    tables = _tables(outcome.results, context)
    if not tables:
        raise EngineError(t("pipeline.no_table"), hint=t("pipeline.no_table.hint"))
    columns = [column.key for column in settings.columns]
    context.emit(preview_table(tables, columns, settings.numeric_column_names()))
    if inputs.preview:
        count = sum(len(table.rows) for table in tables)
        summary = t("pipeline.preview_summary", rows=count, tables=len(tables))
        return ModuleResult(summary=summary, preview=True)
    target = _target(inputs, settings, moment)
    context.emit(LogEvent(message=t("pipeline.writing", name=target.name)))
    with writing_output(target) as draft:
        count = export_submissions(tables, columns, draft)
    summary = t("pipeline.summary", rows=count, tables=len(tables), files=len(sources))
    return ModuleResult(summary=summary, outputs=[target])


def _without_duplicates(paths: list[Path], context: RunContext) -> list[Path]:
    result = deduplicate(paths)
    for duplicate in result.duplicates:
        message = t("pipeline.duplicate", name=duplicate.same_as.name)
        context.emit(WarningEvent(message=message, file=str(duplicate.path)))
    for unreadable in result.unreadable:
        message = t("pipeline.unreadable_source")
        hint = t("pipeline.unreadable_source.hint")
        context.emit(WarningEvent(message=message, file=str(unreadable), hint=hint))
    if not result.unique:
        raise EngineError(t("pipeline.no_source"), hint=t("pipeline.unreadable_source.hint"))
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

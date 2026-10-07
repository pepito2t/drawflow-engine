from datetime import datetime
from functools import partial
from pathlib import Path

from engine.core.anomalies import emit_anomalies
from engine.core.batch import process_batch
from engine.core.cache import resolve_cache_root
from engine.core.contract import ModuleResult, RunContext
from engine.core.errors import EngineError
from engine.core.events import LogEvent
from engine.core.naming import naming_values, output_target, writing_output
from engine.core.settings import load_section
from engine.modules.dwg_diff.export import export_diff
from engine.modules.dwg_diff.messages import t
from engine.modules.dwg_diff.schema import DwgDiffInputs
from engine.modules.dwg_diff.service import (
    DOCUMENT_TYPE,
    compare,
    describe_result,
    preview_table,
)
from engine.modules.dwg_diff.settings import DwgDiffSettings
from engine.parts.collect import collect_plans
from engine.parts.listing import PartsList, build_parts_list
from engine.parts.oda import is_dxf, require_oda
from engine.parts.reader import RawPart
from engine.parts.settings import PartsListSettings
from engine.parts.worker import FileExtraction, extract_file

OUTPUT_EXTENSION = "xlsx"
PARTS_LIST_SECTION = ("dwg-parts", t("pipeline.parts_list_section"))
BEFORE_SIDE = "A"
AFTER_SIDE = "B"


def run_diff(inputs: DwgDiffInputs, context: RunContext, moment: datetime) -> ModuleResult:
    settings = context.settings_as(DwgDiffSettings)
    norm = load_section(PartsListSettings, *PARTS_LIST_SECTION, context.document)
    emit = context.emit
    before_plans = collect_plans(
        inputs.before_files, inputs.before_folders, recursive=inputs.recursive, emit=emit
    )
    after_plans = collect_plans(
        inputs.after_files, inputs.after_folders, recursive=inputs.recursive, emit=emit
    )
    worker = _worker(context, [*before_plans, *after_plans])
    before = _parts_list(before_plans, worker, context, norm, BEFORE_SIDE)
    after = _parts_list(after_plans, worker, context, norm, AFTER_SIDE)
    report = compare(before, after, settings.key_column_names(), settings.increment())
    emit(preview_table(report))
    if inputs.preview:
        return ModuleResult(
            summary=t("pipeline.preview_summary", summary=describe_result(report)), preview=True
        )
    target = _target(inputs, settings, moment)
    emit(LogEvent(message=t("pipeline.writing", name=target.name)))
    with writing_output(target):
        export_diff(report, target)
    return ModuleResult(summary=describe_result(report), outputs=[target])


def _worker(context: RunContext, plans: list[Path]) -> partial[FileExtraction]:
    needs_oda = any(not is_dxf(plan) for plan in plans)
    return partial(
        extract_file,
        oda_executable=require_oda(context.general) if needs_oda else None,
        cache_root=resolve_cache_root(context.general),
    )


def _parts_list(
    plans: list[Path],
    worker: partial[FileExtraction],
    context: RunContext,
    norm: PartsListSettings,
    side: str,
) -> PartsList:
    label = t("pipeline.side_label", side=side)
    outcome = process_batch(
        plans,
        worker,
        batch_size=context.general.batch_size,
        emit=context.emit,
        label=label,
        settings_file=context.settings_file,
    )
    if not outcome.results:
        raise EngineError(t("pipeline.no_file", side=side), hint=t("pipeline.no_file_hint"))
    parts: list[RawPart] = []
    for path, extraction in outcome.results:
        emit_anomalies(context.emit, extraction.warnings, path)
        parts.extend(extraction.parts)
    parts_list = build_parts_list(parts, norm)
    emit_anomalies(context.emit, parts_list.warnings, None)
    return parts_list


def _target(inputs: DwgDiffInputs, settings: DwgDiffSettings, moment: datetime) -> Path:
    values = naming_values(moment, projet=inputs.project.strip(), type=DOCUMENT_TYPE)
    return output_target(
        inputs.output_folder, settings.file_name_template, values, OUTPUT_EXTENSION
    )

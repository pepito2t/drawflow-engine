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
from engine.modules.dwg_parts.collect import collect_plans
from engine.modules.dwg_parts.export import export_parts
from engine.modules.dwg_parts.oda import is_dxf, require_oda
from engine.modules.dwg_parts.reader import RawPart
from engine.modules.dwg_parts.schema import DwgPartsInputs
from engine.modules.dwg_parts.service import (
    DOCUMENT_TYPE,
    build_parts_list,
    describe_result,
    preview_table,
)
from engine.modules.dwg_parts.settings import DwgPartsSettings
from engine.modules.dwg_parts.worker import FileExtraction, extract_file

OUTPUT_EXTENSION = "xlsx"
READ_LABEL = "Lecture"


def run_parts_list(inputs: DwgPartsInputs, context: RunContext, moment: datetime) -> ModuleResult:
    settings = context.settings_as(DwgPartsSettings)
    emit = context.emit
    plans = collect_plans(inputs.files, inputs.folders, recursive=inputs.recursive, emit=emit)
    needs_oda = any(not is_dxf(plan) for plan in plans)
    worker = partial(
        extract_file,
        oda_executable=require_oda(context.general) if needs_oda else None,
        cache_root=resolve_cache_root(context.general),
    )
    outcome = process_batch(
        plans, worker, batch_size=context.general.batch_size, emit=emit, label=READ_LABEL
    )
    if not outcome.results:
        raise EngineError(
            "Aucun plan n'a pu être lu.", hint="Consultez les avertissements du journal."
        )
    parts_list = build_parts_list(_flatten(outcome.results, context), settings)
    emit_anomalies(emit, parts_list.warnings, None)
    emit(preview_table(parts_list))
    if inputs.preview:
        summary = describe_result(parts_list, len(outcome.results), len(plans))
        return ModuleResult(summary=f"Aperçu : {summary}", preview=True)
    target = _target(inputs, settings, plans, moment)
    emit(LogEvent(message=f"Écriture de {target.name}"))
    with writing_output(target):
        export_parts(parts_list.lines, parts_list.headers, target, inputs.template, settings)
    summary = describe_result(parts_list, len(outcome.results), len(plans))
    return ModuleResult(summary=summary, outputs=[target])


def _flatten(results: list[tuple[Path, FileExtraction]], context: RunContext) -> list[RawPart]:
    parts: list[RawPart] = []
    for path, extraction in results:
        emit_anomalies(context.emit, extraction.warnings, path)
        parts.extend(extraction.parts)
    return parts


def _target(
    inputs: DwgPartsInputs, settings: DwgPartsSettings, plans: list[Path], moment: datetime
) -> Path:
    source = plans[0].stem if len(plans) == 1 else ""
    values = naming_values(moment, projet=inputs.project.strip(), type=DOCUMENT_TYPE, source=source)
    return output_target(
        inputs.output_folder, settings.file_name_template, values, OUTPUT_EXTENSION
    )

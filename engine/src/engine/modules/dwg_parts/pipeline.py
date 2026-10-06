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
from engine.modules.dwg_parts.export import export_parts
from engine.modules.dwg_parts.messages import t
from engine.modules.dwg_parts.schema import DwgPartsInputs
from engine.modules.dwg_parts.service import (
    DOCUMENT_TYPE,
    FILES_PROJECT,
    describe_result,
    merge_projects,
    preview_table,
    total_of,
)
from engine.parts.collect import collect_plans
from engine.parts.listing import PartsList, build_parts_list
from engine.parts.oda import is_dxf, require_oda
from engine.parts.reader import RawPart
from engine.parts.settings import PartsListSettings
from engine.parts.worker import FileExtraction, extract_file

OUTPUT_EXTENSION = "xlsx"
READ_LABEL = t("pipeline.read_label")


def run_parts_list(inputs: DwgPartsInputs, context: RunContext, moment: datetime) -> ModuleResult:
    settings = context.settings_as(PartsListSettings)
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
        raise EngineError(t("pipeline.no_file"), hint=t("pipeline.no_file_hint"))
    by_project = _by_project(inputs, outcome.results, context, settings)
    parts_list = merge_projects(by_project) if inputs.multi_project else by_project[0][1]
    emit_anomalies(emit, parts_list.warnings, None)
    emit(preview_table(parts_list))
    if inputs.preview:
        summary = describe_result(parts_list, len(outcome.results), len(plans))
        return ModuleResult(summary=t("pipeline.preview_summary", summary=summary), preview=True)
    target = _target(inputs, settings, plans, moment)
    emit(LogEvent(message=t("pipeline.writing", name=target.name)))
    total = total_of(by_project) if inputs.multi_project else None
    with writing_output(target):
        export_parts(
            parts_list.lines,
            parts_list.headers,
            target,
            inputs.template,
            settings,
            total=(total.headers, total.lines) if total else None,
        )
    summary = describe_result(parts_list, len(outcome.results), len(plans))
    return ModuleResult(summary=summary, outputs=[target])


def _by_project(
    inputs: DwgPartsInputs,
    results: list[tuple[Path, FileExtraction]],
    context: RunContext,
    settings: PartsListSettings,
) -> list[tuple[str, PartsList]]:
    """One parts list per project; a single project unless each folder is one."""
    groups: dict[str, list[RawPart]] = {}
    for path, extraction in results:
        emit_anomalies(context.emit, extraction.warnings, path)
        project = _project_of(path, inputs) if inputs.multi_project else inputs.project
        groups.setdefault(project, []).extend(extraction.parts)
    return [(project, build_parts_list(parts, settings)) for project, parts in groups.items()]


def _project_of(plan: Path, inputs: DwgPartsInputs) -> str:
    """Plans from a folder belong to that folder's project; loose files to the named one."""
    for folder in inputs.folders:
        if folder == plan.parent or folder in plan.parents:
            return folder.name
    return inputs.project.strip() or FILES_PROJECT


def _target(
    inputs: DwgPartsInputs, settings: PartsListSettings, plans: list[Path], moment: datetime
) -> Path:
    source = plans[0].stem if len(plans) == 1 else ""
    values = naming_values(moment, projet=inputs.project.strip(), type=DOCUMENT_TYPE, source=source)
    return output_target(
        inputs.output_folder, settings.file_name_template, values, OUTPUT_EXTENSION
    )

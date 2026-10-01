from datetime import datetime
from functools import partial
from pathlib import Path

from engine.core.batch import process_batch
from engine.core.collect import collect_files
from engine.core.contract import ModuleResult, RunContext
from engine.core.errors import EngineError
from engine.core.events import LogEvent, WarningEvent
from engine.core.naming import naming_values, render_file_name, unique_output_path
from engine.modules.pdf_report.docx_render import render_report
from engine.modules.pdf_report.report import PlanData, build_context
from engine.modules.pdf_report.schema import PdfReportInputs
from engine.modules.pdf_report.settings import PdfReportSettings
from engine.modules.pdf_report.worker import PlanExtraction, extract_plan

PDF_SUFFIXES = frozenset({".pdf"})
PDF_KIND = "PDF"
DOCUMENT_TYPE = "rapport"
OUTPUT_EXTENSION = "docx"
READ_LABEL = "Lecture"


def run_report(inputs: PdfReportInputs, context: RunContext, moment: datetime) -> ModuleResult:
    settings = context.settings_as(PdfReportSettings)
    plans = collect_files(
        inputs.files,
        inputs.folders,
        suffixes=PDF_SUFFIXES,
        kind=PDF_KIND,
        recursive=inputs.recursive,
        emit=context.emit,
    )
    outcome = process_batch(
        plans,
        partial(extract_plan, settings=settings),
        batch_size=context.general.batch_size,
        emit=context.emit,
        label=READ_LABEL,
    )
    if not outcome.results:
        raise EngineError(
            "Aucun PDF n'a pu être lu.", hint="Consultez les avertissements du journal."
        )
    plan_data = _plan_data(outcome.results, context)
    target = _target(inputs, settings, plans, moment)
    context.emit(LogEvent(message=f"Écriture de {target.name}"))
    report = build_context(plan_data, settings.fields, inputs.project.strip(), moment)
    render_report(inputs.template, report, target)
    summary = f"Rapport de {len(plan_data)} plan(s) ({len(plan_data)}/{len(plans)} lu(s))"
    return ModuleResult(summary=summary, outputs=[target])


def _plan_data(results: list[tuple[Path, PlanExtraction]], context: RunContext) -> list[PlanData]:
    for path, extraction in results:
        for warning in extraction.warnings:
            context.emit(WarningEvent(message=warning, file=str(path)))
    return [extraction.plan for _, extraction in results]


def _target(
    inputs: PdfReportInputs, settings: PdfReportSettings, plans: list[Path], moment: datetime
) -> Path:
    source = plans[0].stem if len(plans) == 1 else ""
    values = naming_values(moment, projet=inputs.project.strip(), type=DOCUMENT_TYPE, source=source)
    file_name = render_file_name(settings.file_name_template, values, OUTPUT_EXTENSION)
    return unique_output_path(inputs.output_folder, file_name)

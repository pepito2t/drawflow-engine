from datetime import datetime
from functools import partial
from pathlib import Path

from engine.core.anomalies import emit_anomalies
from engine.core.batch import process_batch
from engine.core.collect import collect_files
from engine.core.contract import ModuleResult, RunContext
from engine.core.errors import EngineError
from engine.core.events import LogEvent
from engine.core.naming import naming_values, output_target, writing_output
from engine.modules.pdf_report.docx_render import render_report
from engine.modules.pdf_report.messages import t
from engine.modules.pdf_report.report import PlanData, build_context
from engine.modules.pdf_report.schema import PdfReportInputs
from engine.modules.pdf_report.settings import PdfReportSettings
from engine.modules.pdf_report.worker import PlanExtraction, extract_plan

PDF_SUFFIXES = frozenset({".pdf"})
PDF_KIND = "PDF"
DOCUMENT_TYPE = "rapport"
OUTPUT_EXTENSION = "docx"


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
        label=t("pipeline.read_label"),
        settings_file=context.settings_file,
    )
    if not outcome.results:
        raise EngineError(t("pipeline.nothing_read"), hint=t("pipeline.nothing_read.hint"))
    plan_data = _plan_data(outcome.results, context)
    target = _target(inputs, settings, plans, moment)
    context.emit(LogEvent(message=t("pipeline.writing", name=target.name)))
    report = build_context(plan_data, settings.fields, inputs.project.strip(), moment)
    with writing_output(target):
        render_report(inputs.template, report, target)
    summary = t("pipeline.summary", count=len(plan_data), read=len(plan_data), total=len(plans))
    return ModuleResult(summary=summary, outputs=[target])


def _plan_data(results: list[tuple[Path, PlanExtraction]], context: RunContext) -> list[PlanData]:
    for path, extraction in results:
        emit_anomalies(context.emit, extraction.warnings, path)
    return [extraction.plan for _, extraction in results]


def _target(
    inputs: PdfReportInputs, settings: PdfReportSettings, plans: list[Path], moment: datetime
) -> Path:
    source = plans[0].stem if len(plans) == 1 else ""
    values = naming_values(moment, projet=inputs.project.strip(), type=DOCUMENT_TYPE, source=source)
    return output_target(
        inputs.output_folder, settings.file_name_template, values, OUTPUT_EXTENSION
    )

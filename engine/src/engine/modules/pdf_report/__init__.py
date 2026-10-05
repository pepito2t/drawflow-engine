from datetime import datetime

from engine.core.contract import EngineModule, ModuleResult, RunContext
from engine.modules.pdf_report.manifest import MANIFEST
from engine.modules.pdf_report.schema import PdfReportInputs
from engine.modules.pdf_report.settings import PdfReportSettings


def _run(inputs: PdfReportInputs, context: RunContext) -> ModuleResult:
    # Lazy: the readers pull in heavy libraries that listing modules or settings never needs.
    from engine.modules.pdf_report.pipeline import run_report

    return run_report(inputs, context, datetime.now())


MODULE = EngineModule(
    manifest=MANIFEST,
    inputs_model=PdfReportInputs,
    run=_run,
    settings_model=PdfReportSettings,
)

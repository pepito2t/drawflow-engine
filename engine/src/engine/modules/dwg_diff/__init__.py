from datetime import datetime

from engine.core.contract import EngineModule, ModuleResult, RunContext
from engine.modules.dwg_diff.manifest import MANIFEST
from engine.modules.dwg_diff.schema import DwgDiffInputs
from engine.modules.dwg_diff.settings import DwgDiffSettings


def _run(inputs: DwgDiffInputs, context: RunContext) -> ModuleResult:
    # Lazy: the readers pull in heavy libraries that listing modules or settings never needs.
    from engine.modules.dwg_diff.pipeline import run_diff

    return run_diff(inputs, context, datetime.now())


MODULE = EngineModule(
    manifest=MANIFEST,
    inputs_model=DwgDiffInputs,
    run=_run,
    settings_model=DwgDiffSettings,
)

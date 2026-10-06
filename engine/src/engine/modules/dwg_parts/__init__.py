from datetime import datetime

from engine.core.contract import EngineModule, ModuleResult, RunContext
from engine.modules.dwg_parts.manifest import MANIFEST
from engine.modules.dwg_parts.schema import DwgPartsInputs
from engine.parts.settings import PartsListSettings


def _run(inputs: DwgPartsInputs, context: RunContext) -> ModuleResult:
    # Lazy: the readers pull in heavy libraries that listing modules or settings never needs.
    from engine.modules.dwg_parts.pipeline import run_parts_list

    return run_parts_list(inputs, context, datetime.now())


MODULE = EngineModule(
    manifest=MANIFEST,
    inputs_model=DwgPartsInputs,
    run=_run,
    settings_model=PartsListSettings,
)

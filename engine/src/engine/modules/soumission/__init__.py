from datetime import datetime

from engine.core.contract import EngineModule, ModuleResult, RunContext
from engine.modules.soumission.manifest import MANIFEST
from engine.modules.soumission.schema import SoumissionInputs
from engine.modules.soumission.settings import SoumissionSettings


def _run(inputs: SoumissionInputs, context: RunContext) -> ModuleResult:
    # Lazy: the readers pull in heavy libraries that listing modules or settings never needs.
    from engine.modules.soumission.pipeline import run_soumission

    return run_soumission(inputs, context, datetime.now())


MODULE = EngineModule(
    manifest=MANIFEST,
    inputs_model=SoumissionInputs,
    run=_run,
    settings_model=SoumissionSettings,
)

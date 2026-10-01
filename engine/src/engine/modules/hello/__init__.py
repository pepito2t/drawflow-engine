from datetime import datetime

from engine.core.contract import EngineModule, ModuleResult, RunContext
from engine.modules.hello import service
from engine.modules.hello.adapters import FileSystemGreetingWriter
from engine.modules.hello.manifest import MANIFEST
from engine.modules.hello.schema import HelloInputs
from engine.modules.hello.settings import HelloSettings


def _run(inputs: HelloInputs, context: RunContext) -> ModuleResult:
    settings = context.settings_as(HelloSettings)
    writer = FileSystemGreetingWriter()
    return service.run(inputs, context.emit, settings, writer, datetime.now())


MODULE = EngineModule(
    manifest=MANIFEST,
    inputs_model=HelloInputs,
    run=_run,
    settings_model=HelloSettings,
)

from engine.core.contract import EngineModule, ModuleResult, RunContext
from engine.modules.hello import service
from engine.modules.hello.adapters import FileSystemGreetingWriter
from engine.modules.hello.manifest import MANIFEST
from engine.modules.hello.schema import HelloInputs


def _run(inputs: HelloInputs, context: RunContext) -> ModuleResult:
    return service.run(inputs, context.emit, FileSystemGreetingWriter())


MODULE = EngineModule(manifest=MANIFEST, inputs_model=HelloInputs, run=_run)

from engine.core.contract import EngineModule, ModuleResult
from engine.core.events import Emit
from engine.modules.hello import service
from engine.modules.hello.adapters import FileSystemGreetingWriter
from engine.modules.hello.manifest import MANIFEST
from engine.modules.hello.schema import HelloInputs


def _run(inputs: HelloInputs, emit: Emit) -> ModuleResult:
    return service.run(inputs, emit, FileSystemGreetingWriter())


MODULE = EngineModule(manifest=MANIFEST, inputs_model=HelloInputs, run=_run)

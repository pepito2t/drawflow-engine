from pathlib import Path
from typing import Protocol

from engine.core.contract import ModuleResult
from engine.core.events import Emit, LogEvent, ProgressEvent
from engine.modules.hello.schema import HelloInputs

GREETING_FILE_NAME = "bonjour.txt"
TOTAL_STEPS = 2


class GreetingWriter(Protocol):
    def write_text(self, path: Path, content: str) -> None: ...


def build_greeting(name: str) -> str:
    return f"Bonjour {name.strip()} !"


def run(inputs: HelloInputs, emit: Emit, writer: GreetingWriter) -> ModuleResult:
    emit(ProgressEvent(current=0, total=TOTAL_STEPS, message="Préparation du message"))
    greeting = build_greeting(inputs.name)
    emit(LogEvent(message=greeting))
    emit(ProgressEvent(current=1, total=TOTAL_STEPS, message="Écriture du fichier"))
    output_path = inputs.output_folder / GREETING_FILE_NAME
    writer.write_text(output_path, greeting)
    emit(ProgressEvent(current=TOTAL_STEPS, total=TOTAL_STEPS, message="Terminé"))
    return ModuleResult(summary=f"Message écrit dans {output_path.name}", outputs=[output_path])

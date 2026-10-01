from datetime import datetime
from pathlib import Path
from typing import Protocol

from engine.core.contract import ModuleResult
from engine.core.events import Emit, LogEvent, ProgressEvent
from engine.core.naming import naming_values, render_file_name
from engine.modules.hello.schema import HelloInputs
from engine.modules.hello.settings import HelloSettings

DOCUMENT_TYPE = "test"
OUTPUT_EXTENSION = "txt"
TOTAL_STEPS = 2


class GreetingWriter(Protocol):
    def write_text(self, folder: Path, file_name: str, content: str) -> Path: ...


def build_greeting(name: str) -> str:
    return f"Bonjour {name.strip()} !"


def build_file_name(settings: HelloSettings, moment: datetime) -> str:
    values = naming_values(moment, type=DOCUMENT_TYPE)
    return render_file_name(settings.file_name_template, values, OUTPUT_EXTENSION)


def run(
    inputs: HelloInputs,
    emit: Emit,
    settings: HelloSettings,
    writer: GreetingWriter,
    moment: datetime,
) -> ModuleResult:
    emit(ProgressEvent(current=0, total=TOTAL_STEPS, message="Préparation du message"))
    greeting = build_greeting(inputs.name)
    emit(LogEvent(message=greeting))
    emit(ProgressEvent(current=1, total=TOTAL_STEPS, message="Écriture du fichier"))
    output_path = writer.write_text(
        inputs.output_folder, build_file_name(settings, moment), greeting
    )
    emit(ProgressEvent(current=TOTAL_STEPS, total=TOTAL_STEPS, message="Terminé"))
    return ModuleResult(summary=f"Message écrit dans {output_path.name}", outputs=[output_path])

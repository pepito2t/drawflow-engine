import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from engine.core.contract import ModuleResult, RunContext
from engine.core.errors import InputFileError, InvalidInputError
from engine.core.events import Emit, ResultEvent
from engine.core.registry import AnyModule
from engine.core.settings import RunSettings
from engine.core.validation import describe_validation_error


def read_input_file(path: Path) -> dict[str, Any]:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InputFileError("Le fichier de paramètres est introuvable.", file=path) from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputFileError(
            "Le fichier de paramètres est illisible.",
            file=path,
            hint="Relancez la fonctionnalité depuis l'application.",
        ) from error
    if not isinstance(content, dict):
        raise InputFileError("Le fichier de paramètres doit contenir un objet JSON.", file=path)
    return content


def run_module(
    module: AnyModule, raw_inputs: dict[str, Any], settings: RunSettings, emit: Emit
) -> ModuleResult:
    inputs = _validate_inputs(module, raw_inputs)
    context = RunContext(emit=emit, general=settings.general, module_settings=settings.module)
    result = module.run(inputs, context)
    emit(ResultEvent(summary=result.summary, outputs=[str(path) for path in result.outputs]))
    return result


def _validate_inputs(module: AnyModule, raw_inputs: dict[str, Any]) -> Any:
    try:
        return module.inputs_model.model_validate(raw_inputs)
    except ValidationError as error:
        raise InvalidInputError(
            "Champs invalides : " + describe_validation_error(module.inputs_model, error),
            hint="Corrigez les champs indiqués puis relancez.",
        ) from error

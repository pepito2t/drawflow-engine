import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from pydantic.fields import FieldInfo

from engine.core.contract import ModuleResult
from engine.core.errors import InputFileError, InvalidInputError
from engine.core.events import Emit, ResultEvent
from engine.core.registry import AnyModule


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


def run_module(module: AnyModule, raw_inputs: dict[str, Any], emit: Emit) -> ModuleResult:
    inputs = _validate_inputs(module, raw_inputs)
    result = module.run(inputs, emit)
    emit(ResultEvent(summary=result.summary, outputs=[str(path) for path in result.outputs]))
    return result


def _validate_inputs(module: AnyModule, raw_inputs: dict[str, Any]) -> Any:
    try:
        return module.inputs_model.model_validate(raw_inputs)
    except ValidationError as error:
        raise InvalidInputError(
            "Champs invalides : " + _describe(module, error),
            hint="Corrigez les champs indiqués puis relancez.",
        ) from error


def _describe(module: AnyModule, error: ValidationError) -> str:
    return "; ".join(
        f"{_field_label(module, issue['loc'])} ({issue['msg']})" for issue in error.errors()
    )


def _field_label(module: AnyModule, location: tuple[int | str, ...]) -> str:
    if not location:
        return "formulaire"
    field: FieldInfo | None = module.inputs_model.model_fields.get(str(location[0]))
    if field is None or field.title is None:
        return ".".join(str(part) for part in location)
    return field.title

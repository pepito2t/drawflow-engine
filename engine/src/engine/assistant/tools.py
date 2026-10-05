"""Read-only views of Drawflow exposed to the assistant as MCP tools."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from engine.assistant.events import Proposal
from engine.core.errors import InvalidInputError
from engine.core.presets import PresetStore
from engine.core.registry import discover_modules, get_module
from engine.core.templates import TemplateLibrary
from engine.core.validation import describe_validation_error
from engine.requests import template_users


def describe_features() -> dict[str, Any]:
    return {
        "features": [
            {
                "id": module.manifest.id,
                "name": module.manifest.name,
                "description": module.manifest.description,
                "instructions": module.manifest.instructions,
                "inputs_schema": module.inputs_model.model_json_schema(),
            }
            for module in discover_modules().values()
        ]
    }


def describe_presets(settings: Path) -> dict[str, Any]:
    return {
        "presets": [
            {"id": preset.id, "name": preset.name, "feature": preset.module}
            for preset in PresetStore(settings).presets()
        ]
    }


def describe_templates(settings: Path) -> dict[str, Any]:
    return TemplateLibrary(settings).describe(template_users())


def propose_preset_run(settings: Path, preset_id: str) -> dict[str, Any]:
    preset = next((p for p in PresetStore(settings).presets() if p.id == preset_id), None)
    if preset is None:
        raise InvalidInputError(
            f"Le préréglage « {preset_id} » n'existe pas.", hint="Utilise list_presets."
        )
    module = get_module(preset.module)
    proposal = Proposal(
        kind="preset",
        feature=module.manifest.id,
        feature_name=module.manifest.name,
        label=preset.name,
        preset_id=preset.id,
        inputs=preset.inputs,
    )
    return {"proposal": proposal.model_dump(mode="json")}


def propose_feature_run(feature_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    module = get_module(feature_id)
    try:
        validated = module.inputs_model.model_validate(inputs)
    except ValidationError as error:
        raise InvalidInputError(
            f"Entrées invalides pour « {module.manifest.name} ».",
            hint=f"{describe_validation_error(module.inputs_model, error)}. "
            "Consulte inputs_schema avec list_features.",
        ) from error
    proposal = Proposal(
        kind="feature",
        feature=module.manifest.id,
        feature_name=module.manifest.name,
        label=module.manifest.name,
        inputs=validated.model_dump(mode="json"),
    )
    return {"proposal": proposal.model_dump(mode="json")}

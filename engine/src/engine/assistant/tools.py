"""Read-only views of Drawflow exposed to the assistant as MCP tools."""

from pathlib import Path
from typing import Any

from engine.core.presets import PresetStore
from engine.core.registry import discover_modules
from engine.core.templates import TemplateLibrary
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

"""Read-only views of Drawflow exposed to the assistant as MCP tools."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from engine.assistant.events import Proposal
from engine.core.errors import InvalidInputError
from engine.core.guide import read_section, sections
from engine.core.history import HistoryStore
from engine.core.presets import PresetStore
from engine.core.registry import discover_modules, get_module
from engine.core.templates import TemplateLibrary
from engine.core.validation import describe_validation_error
from engine.modules.soumission.headers import (
    SECTION_ID,
    SECTION_TITLE,
    current_settings,
    inspect_headers,
    validate_additions,
)
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


def inspect_submission(settings: Path, path: str) -> dict[str, Any]:
    return inspect_headers(Path(path), current_settings(settings))


def propose_column_synonyms(settings: Path, additions: dict[str, list[str]]) -> dict[str, Any]:
    cleaned = validate_additions(current_settings(settings), additions)
    proposal = Proposal(
        kind="synonyms",
        feature=SECTION_ID,
        feature_name=SECTION_TITLE,
        label="En-têtes reconnus",
        inputs={"columns": cleaned},
    )
    return {"proposal": proposal.model_dump(mode="json")}


RECENT_RUNS = 5
MAX_LISTED_RUNS = 50


def describe_runs(settings: Path, limit: int = RECENT_RUNS) -> dict[str, Any]:
    """The history as the assistant may quote it: ids first, so it can read one in detail."""
    count = max(1, min(limit, MAX_LISTED_RUNS))
    return {"runs": [_run_summary(entry) for entry in HistoryStore(settings).entries()[:count]]}


def describe_run(settings: Path, run_id: str) -> dict[str, Any]:
    """Everything recorded for one run: inputs, outputs and each warning with its place."""
    entry = next((e for e in HistoryStore(settings).entries() if e.id == run_id), None)
    if entry is None:
        raise InvalidInputError(
            f"Aucun traitement « {run_id} » dans l'historique.", hint="Utilise list_runs."
        )
    return {
        **_run_summary(entry),
        "inputs": entry.inputs,
        "duration_ms": entry.duration_ms,
        "warnings": [warning.model_dump(mode="json") for warning in entry.warnings],
    }


def _run_summary(entry: Any) -> dict[str, Any]:
    return {
        "id": entry.id,
        "started_at": entry.started_at,
        "feature": entry.module,
        "feature_name": entry.module_name,
        "status": entry.status,
        "summary": entry.summary,
        "error": entry.error,
        "outputs": entry.outputs,
        "warnings": len(entry.warnings),
    }


def describe_today(settings: Path) -> dict[str, Any]:
    """What the user sees on the Today screen: last runs and one-click presets."""
    recent = HistoryStore(settings).entries()[:RECENT_RUNS]
    return {
        "recent_runs": [_run_summary(entry) for entry in recent],
        "presets": describe_presets(settings)["presets"],
    }


def help_topics() -> dict[str, Any]:
    return {"topics": [{"id": section.id, "title": section.title} for section in sections()]}


def help_section(topic: str) -> dict[str, Any]:
    section = read_section(topic)
    return {"id": section.id, "title": section.title, "markdown": section.markdown}

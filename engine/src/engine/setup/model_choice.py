"""The model the setup works with: the one chosen in Settings, else the one fitting the memory."""

from pathlib import Path

from engine.assistant.catalog import recommend
from engine.core.registry import discover_modules
from engine.core.settings import (
    ASSISTANT_SECTION_ID,
    load_assistant_settings,
    read_document,
    save_settings,
)
from engine.core.settings_models import AssistantSettings
from engine.setup.machine import Machine

MODEL_FIELD = "model"


def chosen_model(settings: Path) -> str | None:
    chosen = read_document(settings).get(ASSISTANT_SECTION_ID, {}).get(MODEL_FIELD)
    return str(chosen) if chosen else None


def effective_assistant_settings(settings: Path, machine: Machine) -> AssistantSettings:
    assistant = load_assistant_settings(settings)
    if chosen_model(settings) is not None:
        return assistant
    return assistant.model_copy(update={MODEL_FIELD: recommend(machine.memory_bytes)})


def remember_model(settings: Path, assistant: AssistantSettings) -> None:
    section = assistant.model_dump(mode="json")
    save_settings(settings, {ASSISTANT_SECTION_ID: section}, discover_modules())

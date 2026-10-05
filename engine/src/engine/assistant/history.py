"""The current conversation, kept on this computer between two launches."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from engine.assistant.conversation import MAX_HISTORY_MESSAGES, ChatMessage
from engine.core.errors import InvalidInputError, OutputWriteError
from engine.core.json_files import write_json_atomically

HISTORY_FILE = "assistant-history.json"


class SavedConversation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    messages: list[ChatMessage] = []


def read_history(settings: Path) -> dict[str, Any]:
    path = _history_file(settings)
    if not path.is_file():
        return SavedConversation().model_dump()
    try:
        saved = SavedConversation.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, ValidationError):
        # A lost conversation is not worth blocking the assistant: it starts afresh.
        return {**SavedConversation().model_dump(), "warning": "Conversation précédente illisible."}
    return saved.model_dump()


def save_history(settings: Path, raw: dict[str, Any]) -> dict[str, Any]:
    try:
        conversation = SavedConversation.model_validate(raw)
    except ValidationError as error:
        raise InvalidInputError("Conversation invalide.", hint=str(error)) from error
    kept = SavedConversation(messages=conversation.messages[-MAX_HISTORY_MESSAGES:])
    path = _history_file(settings)
    try:
        write_json_atomically(path, kept.model_dump())
    except OSError as error:
        raise OutputWriteError("Impossible d'enregistrer la conversation.", file=path) from error
    return kept.model_dump()


def _history_file(settings: Path) -> Path:
    return settings.parent / HISTORY_FILE

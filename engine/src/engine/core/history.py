"""What was run, with what, and what came out: reopen a result or run it again later."""

import json
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError

from engine.core.contract import ModuleResult
from engine.core.errors import EngineError, InvalidInputError, OutputWriteError
from engine.core.events import Emit, Event, WarningEvent
from engine.core.json_files import write_json_atomically
from engine.core.messages import t
from engine.core.registry import AnyModule
from engine.core.stats import StatsStore, count_files

HISTORY_FILE = "history.json"
MAX_ENTRIES = 200
ENTRY_ID_LENGTH = 12
MILLISECONDS = 1000

HISTORY_ACTIONS = {
    "list": "Traitements passés, du plus récent au plus ancien (JSON).",
    "remove": "Retire un traitement de l'historique (JSON).",
    "clear": "Vide l'historique (JSON).",
    "stats": "Compteurs locaux : traitements, fichiers, temps estimé gagné (JSON).",
}

RunStatus = Literal["succeeded", "failed"]


class HistoryError(EngineError):
    pass


class HistoryWarning(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    message: str
    file: str | None = None
    location: str | None = None
    hint: str | None = None


def _as_warning(value: Any) -> Any:
    # Entries written before warnings were structured hold plain messages.
    return {"message": value} if isinstance(value, str) else value


class HistoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[0-9a-f]+$")
    started_at: str
    module: str
    module_name: str
    inputs: dict[str, Any]
    status: RunStatus
    summary: str
    outputs: list[str] = Field(default_factory=list)
    warnings: list[Annotated[HistoryWarning, BeforeValidator(_as_warning)]] = Field(
        default_factory=list
    )
    error: str | None = None
    duration_ms: int


class HistoryStore:
    def __init__(self, settings_file: Path) -> None:
        self.path = settings_file.parent / HISTORY_FILE

    def entries(self) -> list[HistoryEntry]:
        if not self.path.is_file():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [HistoryEntry.model_validate(item) for item in raw]
        except (OSError, json.JSONDecodeError, TypeError, ValidationError) as error:
            raise HistoryError(
                t("history.unreadable"), file=self.path, hint=t("history.unreadable_hint")
            ) from error

    def record(self, entry: HistoryEntry) -> None:
        self._write([entry, *self.entries()][:MAX_ENTRIES])

    def remove(self, entry_id: str) -> None:
        self._write([entry for entry in self.entries() if entry.id != entry_id])

    def clear(self) -> None:
        self._write([])

    def _write(self, entries: list[HistoryEntry]) -> None:
        try:
            write_json_atomically(self.path, [entry.model_dump(mode="json") for entry in entries])
        except OSError as error:
            raise OutputWriteError(t("history.save_failed"), file=self.path) from error


@dataclass(frozen=True)
class UsageCounters:
    store: StatsStore
    minutes_per_file: int


def run_with_history(
    history: HistoryStore | None,
    module: AnyModule,
    raw_inputs: dict[str, Any],
    emit: Emit,
    run: Callable[[Emit], ModuleResult],
    counters: UsageCounters | None = None,
) -> ModuleResult:
    """Runs the module and records the outcome; the run's own error is still raised."""
    if history is None:
        return run(emit)
    warnings: list[HistoryWarning] = []
    started = datetime.now(UTC)
    clock = time.monotonic()

    def observing(event: Event) -> None:
        if isinstance(event, WarningEvent):
            warnings.append(
                HistoryWarning(
                    message=event.message,
                    file=event.file,
                    location=event.location,
                    hint=event.hint,
                )
            )
        emit(event)

    def entry(**outcome: Any) -> HistoryEntry:
        return HistoryEntry(
            id=uuid.uuid4().hex[:ENTRY_ID_LENGTH],
            started_at=started.isoformat(timespec="seconds"),
            module=module.manifest.id,
            module_name=module.manifest.name,
            inputs=raw_inputs,
            warnings=warnings,
            duration_ms=int((time.monotonic() - clock) * MILLISECONDS),
            **outcome,
        )

    try:
        result = run(observing)
    except EngineError as error:
        history.record(entry(status="failed", summary="", error=error.message))
        raise
    if result.preview:
        return result
    history.record(
        entry(
            status="succeeded",
            summary=result.summary,
            outputs=[str(path) for path in result.outputs],
        )
    )
    if counters is not None:
        _count(counters, module, raw_inputs, emit)
    return result


def _count(counters: UsageCounters, module: AnyModule, inputs: dict[str, Any], emit: Emit) -> None:
    try:
        counters.store.record(
            module.manifest.id, module.manifest.name, count_files(inputs), counters.minutes_per_file
        )
    except EngineError as error:
        # The output is already written: a broken counter file must not fail the run.
        file = str(error.file) if error.file is not None else None
        emit(WarningEvent(message=error.message, file=file, hint=error.hint))


def handle_history(action: str, settings_file: Path, request: dict[str, Any]) -> dict[str, Any]:
    store = HistoryStore(settings_file)
    if action == "list":
        return {"entries": [entry.model_dump(mode="json") for entry in store.entries()]}
    if action == "remove":
        entry_id = request.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            raise InvalidInputError(t("history.missing_id"))
        store.remove(entry_id)
        return {"removed": entry_id}
    if action == "clear":
        store.clear()
        return {"cleared": True}
    if action == "stats":
        return StatsStore(settings_file).read().model_dump(mode="json")
    raise InvalidInputError(t("history.unknown_action", action=action))

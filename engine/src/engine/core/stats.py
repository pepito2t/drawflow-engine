"""Local usage counters: how many runs and files, and an estimate of the time they saved."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic.fields import FieldInfo

from engine.core.errors import EngineError, OutputWriteError
from engine.core.fields import UI_KIND_SCHEMA_KEY
from engine.core.json_files import write_json_atomically
from engine.core.messages import t

STATS_FILE = "stats.json"
FILE_KINDS = {"file", "files"}


class StatsError(EngineError):
    pass


class FeatureStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: str
    module_name: str
    runs: int = 0
    files: int = 0
    minutes_saved: int = 0


class UsageStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    since: str | None = None
    features: list[FeatureStats] = Field(default_factory=list)


def count_files(model: type[BaseModel], inputs: dict[str, Any]) -> int:
    """Paths given in the module's file fields; templates and free text never count."""
    total = 0
    for name, field in model.model_fields.items():
        if _ui_kind(field) not in FILE_KINDS:
            continue
        value = inputs.get(name)
        candidates = value if isinstance(value, list) else [value]
        total += sum(1 for item in candidates if isinstance(item, str) and item)
    return total


def _ui_kind(field: FieldInfo) -> str | None:
    extra = field.json_schema_extra
    kind = extra.get(UI_KIND_SCHEMA_KEY) if isinstance(extra, dict) else None
    return kind if isinstance(kind, str) else None


class StatsStore:
    def __init__(self, settings_file: Path) -> None:
        self.path = settings_file.parent / STATS_FILE

    def read(self) -> UsageStats:
        if not self.path.is_file():
            return UsageStats()
        try:
            return UsageStats.model_validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, ValidationError) as error:
            raise StatsError(
                t("stats.unreadable"), file=self.path, hint=t("stats.unreadable_hint")
            ) from error

    def record(self, module: str, module_name: str, files: int, minutes_per_file: int) -> None:
        stats = self.read()
        feature = next((item for item in stats.features if item.module == module), None)
        if feature is None:
            feature = FeatureStats(module=module, module_name=module_name)
            stats.features.append(feature)
        feature.runs += 1
        feature.files += files
        feature.minutes_saved += files * minutes_per_file
        if stats.since is None:
            stats.since = datetime.now(UTC).isoformat(timespec="seconds")
        try:
            write_json_atomically(self.path, stats.model_dump(mode="json"))
        except OSError as error:
            raise OutputWriteError(t("stats.save_failed"), file=self.path) from error

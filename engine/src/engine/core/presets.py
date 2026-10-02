import json
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from engine.core.errors import EngineError, OutputWriteError
from engine.core.registry import AnyModule
from engine.core.validation import describe_validation_error

PRESETS_FILE = "presets.json"
PRESET_ID_LENGTH = 8


class PresetError(EngineError):
    pass


class Preset(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[0-9a-f]+$")
    name: str = Field(min_length=1, max_length=80)
    module: str
    inputs: dict[str, Any]


class PresetStore:
    """Named sets of form values, launchable in one action (Stream Deck keys)."""

    def __init__(self, settings_file: Path) -> None:
        self.path = settings_file.parent / PRESETS_FILE

    def presets(self) -> list[Preset]:
        if not self.path.is_file():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [Preset.model_validate(item) for item in raw]
        except (OSError, json.JSONDecodeError, TypeError, ValidationError) as error:
            raise PresetError(
                "Le fichier des préréglages est illisible ; il n'a pas été modifié.",
                file=self.path,
                hint="Supprimez-le pour repartir d'une liste vide.",
            ) from error

    def save(
        self, module: AnyModule, name: str, inputs: dict[str, Any], preset_id: str | None = None
    ) -> Preset:
        _validate_inputs(module, name, inputs)
        preset = Preset(
            id=preset_id or uuid.uuid4().hex[:PRESET_ID_LENGTH],
            name=name.strip(),
            module=module.manifest.id,
            inputs=inputs,
        )
        others = [existing for existing in self.presets() if existing.id != preset.id]
        if any(existing.name.casefold() == preset.name.casefold() for existing in others):
            raise PresetError(f"Un préréglage « {preset.name} » existe déjà.")
        self._write([*others, preset])
        return preset

    def remove(self, preset_id: str) -> None:
        remaining = [preset for preset in self.presets() if preset.id != preset_id]
        self._write(remaining)

    def _write(self, presets: list[Preset]) -> None:
        temporary = self.path.with_name(f"{self.path.name}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            content = [preset.model_dump(mode="json") for preset in presets]
            temporary.write_text(
                json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporary.replace(self.path)
        except OSError as error:
            raise OutputWriteError(
                "Impossible d'enregistrer les préréglages.", file=self.path
            ) from error


def _validate_inputs(module: AnyModule, name: str, inputs: dict[str, Any]) -> None:
    try:
        module.inputs_model.model_validate(inputs)
    except ValidationError as error:
        raise PresetError(
            f"Préréglage « {name.strip()} » incomplet : "
            f"{describe_validation_error(module.inputs_model, error)}",
            hint="Complétez le formulaire avant de l'enregistrer.",
        ) from error

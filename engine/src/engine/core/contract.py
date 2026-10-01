from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import PydanticUndefined

from engine.core.events import Emit

UiKind = Literal[
    "file",
    "files",
    "folder",
    "folders",
    "output_folder",
    "template",
    "text",
    "bool",
    "enum",
]
UI_KIND_SCHEMA_KEY = "x-ui"
MODULE_ID_PATTERN = r"^[a-z][a-z0-9-]*$"


class ModuleManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=MODULE_ID_PATTERN)
    name: str = Field(min_length=1)
    description: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    order: int = Field(ge=0, description="Position de l'onglet dans l'interface.")
    instructions: list[str] = Field(
        min_length=1, description="Mode d'emploi, une étape par entrée."
    )


class ModuleInputs(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ModuleResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    summary: str
    outputs: list[Path] = Field(default_factory=list)


@dataclass(frozen=True)
class EngineModule[InputsT: ModuleInputs]:
    manifest: ModuleManifest
    inputs_model: type[InputsT]
    run: Callable[[InputsT, Emit], ModuleResult]


def ui_field(
    kind: UiKind,
    *,
    label: str,
    default: Any = PydanticUndefined,
    description: str | None = None,
    **constraints: Any,
) -> Any:
    """Declares a form field; `kind` drives the widget the UI generates."""
    return Field(
        default,
        title=label,
        description=description,
        json_schema_extra={UI_KIND_SCHEMA_KEY: kind},
        **constraints,
    )

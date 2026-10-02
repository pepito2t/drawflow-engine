from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from engine.core.events import Emit
from engine.core.settings_models import GeneralSettings, ModuleSettings

MODULE_ID_PATTERN = r"^[a-z][a-z0-9-]*$"

ModuleIcon = Literal["module", "list", "report", "table", "check"]
TemplateKind = Literal["xlsx", "docx"]


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
    icon: ModuleIcon = Field(default="module", description="Icône de l'onglet.")
    template_kind: TemplateKind | None = Field(
        default=None, description="Type de modèle de sortie accepté (champ « template »)."
    )


class ModuleInputs(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ModuleResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    summary: str
    outputs: list[Path] = Field(default_factory=list)


@dataclass(frozen=True)
class RunContext:
    emit: Emit
    general: GeneralSettings
    module_settings: ModuleSettings | None = None

    def settings_as[SettingsT: ModuleSettings](self, model: type[SettingsT]) -> SettingsT:
        if not isinstance(self.module_settings, model):
            raise TypeError(f"Le module attend des paramètres {model.__name__}.")
        return self.module_settings


@dataclass(frozen=True)
class EngineModule[InputsT: ModuleInputs]:
    manifest: ModuleManifest
    inputs_model: type[InputsT]
    run: Callable[[InputsT, RunContext], ModuleResult]
    settings_model: type[ModuleSettings] | None = None

from typing import Literal

from pydantic import BaseModel, ConfigDict

from engine.setup.machine import OperatingSystem

ItemStatus = Literal["ok", "missing", "optional"]
ActionId = Literal[
    "oda.install",
    "oda.use-detected",
    "oda.open-page",
    "ollama.install",
    "ollama.start",
    "ollama.open-page",
    "model.pull",
    "models.open",
    "streamdock.install-plugin",
    "streamdock.open-page",
]
PackageManager = Literal["winget", "brew"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SetupAction(_Frozen):
    id: ActionId
    label: str
    url: str | None = None


class SetupItem(_Frozen):
    id: str
    label: str
    status: ItemStatus
    detail: str
    actions: list[SetupAction] = []
    help: str | None = None


class SystemInfo(_Frozen):
    os: OperatingSystem
    arch: str
    package_manager: PackageManager | None


class SetupReport(_Frozen):
    system: SystemInfo
    items: list[SetupItem]

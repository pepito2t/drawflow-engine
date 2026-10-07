"""Turns what is found on the computer into a checklist with the actions that fix each item."""

from dataclasses import dataclass
from pathlib import Path

from engine.assistant.catalog import recommend
from engine.core.settings_models import AssistantSettings
from engine.setup.locations import (
    AUTOCAD_PLUGIN,
    DRAWFLOW_PLUGIN,
    find_autocad,
    find_oda,
    ollama_installed,
    stream_dock_folder,
    stream_dock_plugin_installed,
    stream_dock_plugin_version,
)
from engine.setup.machine import Machine
from engine.setup.messages import t
from engine.setup.report import (
    ActionId,
    PackageManager,
    SetupAction,
    SetupItem,
    SetupReport,
    SystemInfo,
)
from engine.setup.stream_dock import AUTOCAD_PLUGIN_REPOSITORY

ACTION_LABELS: dict[ActionId, str] = {
    "oda.install": t("scan.action.install"),
    "oda.use-detected": t("scan.action.use"),
    "oda.open-page": t("scan.action.download_page"),
    "ollama.install": t("scan.action.install"),
    "ollama.start": t("scan.action.start"),
    "ollama.open-page": t("scan.action.download_page"),
    "model.pull": t("scan.action.download"),
    "models.open": t("scan.action.choose_model"),
    "streamdock.install-plugin": t("scan.action.install_plugin"),
    "streamdock.install-autocad-plugin": t("scan.action.install_plugin"),
    "streamdock.open-page": t("scan.action.download_page"),
    "autocad-plugin.open-page": t("scan.action.project_page"),
}
UPDATE_LABEL = t("scan.action.update")
REINSTALL_LABEL = t("scan.action.reinstall")
DOWNLOAD_PAGES: dict[ActionId, str] = {
    "oda.open-page": "https://www.opendesign.com/guestfiles/oda_file_converter",
    "ollama.open-page": "https://ollama.com/download",
    "streamdock.open-page": "https://mirabox.net/pages/download",
    "autocad-plugin.open-page": AUTOCAD_PLUGIN_REPOSITORY,
}


# Sections of docs/guide.md that walk the user through each item.
PREREQUISITES_HELP = "installer-les-prérequis"
STREAM_DOCK_HELP = "piloter-avec-un-stream-dock"


@dataclass(frozen=True)
class ModelServerState:
    reachable: bool
    is_ollama: bool
    available: list[str]


def build_report(
    machine: Machine,
    oda_configured: Path | None,
    assistant: AssistantSettings,
    server: ModelServerState,
    app_version: str | None = None,
    autocad_plugin_latest: str | None = None,
) -> SetupReport:
    system = SystemInfo(os=machine.os, arch=machine.arch, package_manager=_manager(machine))
    recommended = recommend(machine.memory_bytes)
    items = [
        _with_help(_oda_item(machine, system, oda_configured), PREREQUISITES_HELP),
        _with_help(_model_server_item(machine, system, assistant, server), PREREQUISITES_HELP),
        _with_help(_model_item(assistant, server, recommended), PREREQUISITES_HELP),
        _with_help(_stream_dock_item(machine, app_version), STREAM_DOCK_HELP),
        _with_help(_autocad_plugin_item(machine, autocad_plugin_latest), STREAM_DOCK_HELP),
    ]
    return SetupReport(system=system, items=items, recommended_model=recommended)


def _oda_item(machine: Machine, system: SystemInfo, configured: Path | None) -> SetupItem:
    label = "ODA File Converter"
    if configured is not None and machine.is_file(configured):
        return SetupItem(id="oda", label=label, status="ok", detail=str(configured))
    detected = find_oda(machine)
    if detected is not None:
        return SetupItem(
            id="oda",
            label=label,
            status="missing",
            detail=t("scan.oda.installed_not_configured", path=detected),
            actions=_actions("oda.use-detected"),
        )
    return SetupItem(
        id="oda",
        label=label,
        status="missing",
        detail=t("scan.oda.needed"),
        actions=_oda_install_actions(machine),
    )


def _model_server_item(
    machine: Machine, system: SystemInfo, assistant: AssistantSettings, server: ModelServerState
) -> SetupItem:
    label = t("scan.model_server.label")
    if server.reachable:
        name = "Ollama" if server.is_ollama else t("scan.model_server.openai_compatible")
        return SetupItem(
            id="model-server",
            label=label,
            status="ok",
            detail=f"{name} — {assistant.model_server_url}",
        )
    if ollama_installed(machine):
        return SetupItem(
            id="model-server",
            label=label,
            status="missing",
            detail=t("scan.model_server.ollama_down"),
            actions=_actions("ollama.start"),
        )
    return SetupItem(
        id="model-server",
        label=label,
        status="missing",
        detail=t("scan.model_server.ollama_pitch"),
        actions=_ollama_install_actions(system),
    )


def _model_item(
    assistant: AssistantSettings, server: ModelServerState, recommended: str
) -> SetupItem:
    label = t("scan.model.label")
    model = assistant.model
    if not server.reachable:
        return SetupItem(
            id="model",
            label=label,
            status="missing",
            detail=t("scan.model.server_first", model=model),
        )
    if model in server.available:
        return SetupItem(
            id="model", label=label, status="ok", detail=t("scan.model.available", model=model)
        )
    if server.is_ollama:
        return SetupItem(
            id="model",
            label=label,
            status="missing",
            detail=t("scan.model.not_downloaded", model=model, recommended=recommended),
            actions=_actions("model.pull", "models.open"),
        )
    return SetupItem(
        id="model",
        label=label,
        status="missing",
        detail=t("scan.model.not_on_server", model=model),
    )


def _stream_dock_item(machine: Machine, app_version: str | None) -> SetupItem:
    label = t("scan.stream_dock.label")
    if stream_dock_folder(machine) is None:
        return SetupItem(
            id="stream-dock",
            label=label,
            status="optional",
            detail=t("scan.stream_dock.not_installed"),
            actions=_actions("streamdock.open-page"),
        )
    if not stream_dock_plugin_installed(machine):
        return SetupItem(
            id="stream-dock",
            label=label,
            status="optional",
            detail=t("scan.stream_dock.pitch"),
            actions=_actions("streamdock.install-plugin"),
        )
    installed = stream_dock_plugin_version(machine, DRAWFLOW_PLUGIN)
    return _installed_plugin_item(
        "stream-dock", label, "streamdock.install-plugin", installed, app_version
    )


def _autocad_plugin_item(machine: Machine, latest: str | None) -> SetupItem:
    label = t("scan.autocad_plugin.label")
    if stream_dock_folder(machine) is None:
        return SetupItem(
            id="autocad-plugin",
            label=label,
            status="optional",
            detail=t("scan.stream_dock.not_installed"),
            actions=_actions("autocad-plugin.open-page"),
        )
    autocad = (
        t("scan.autocad_plugin.detected")
        if find_autocad(machine) is not None
        else t("scan.autocad_plugin.not_detected")
    )
    if not stream_dock_plugin_installed(machine, AUTOCAD_PLUGIN):
        return SetupItem(
            id="autocad-plugin",
            label=label,
            status="optional",
            detail=t("scan.autocad_plugin.pitch", autocad=autocad),
            actions=_actions("streamdock.install-autocad-plugin", "autocad-plugin.open-page"),
        )
    installed = stream_dock_plugin_version(machine, AUTOCAD_PLUGIN)
    item = _installed_plugin_item(
        "autocad-plugin", label, "streamdock.install-autocad-plugin", installed, latest
    )
    return item.model_copy(update={"detail": f"{item.detail} {autocad}"})


def _installed_plugin_item(
    item_id: str, label: str, install: ActionId, installed: str | None, available: str | None
) -> SetupItem:
    version = (
        t("scan.plugin.version_installed", version=installed)
        if installed
        else t("scan.plugin.installed")
    )
    if available is not None and installed != available:
        return SetupItem(
            id=item_id,
            label=label,
            status="update",
            detail=t("scan.plugin.update_available", version=version, available=available),
            actions=[_action(install, UPDATE_LABEL)],
        )
    return SetupItem(
        id=item_id,
        label=label,
        status="ok",
        detail=t("scan.plugin.restart", version=version),
        actions=[_action(install, REINSTALL_LABEL)],
    )


def _with_help(item: SetupItem, topic: str) -> SetupItem:
    return item.model_copy(update={"help": topic})


def _manager(machine: Machine) -> PackageManager | None:
    if machine.os == "windows" and machine.which("winget") is not None:
        return "winget"
    if machine.os == "macos" and machine.which("brew") is not None:
        return "brew"
    return None


def _ollama_install_actions(system: SystemInfo) -> list[SetupAction]:
    """Windows downloads Ollama's own installer; macOS needs Homebrew for a silent install."""
    if system.os == "windows" or system.package_manager == "brew":
        return _actions("ollama.install", "ollama.open-page")
    return _actions("ollama.open-page")


def _oda_install_actions(machine: Machine) -> list[SetupAction]:
    """ODA ships its own Windows installer; macOS has no silent install, only the page."""
    if machine.os == "windows":
        return _actions("oda.install", "oda.open-page")
    return _actions("oda.open-page")


def _actions(*ids: ActionId) -> list[SetupAction]:
    return [_action(action) for action in ids]


def _action(action: ActionId, label: str | None = None) -> SetupAction:
    return SetupAction(
        id=action, label=label or ACTION_LABELS[action], url=DOWNLOAD_PAGES.get(action)
    )

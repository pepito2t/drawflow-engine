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
    "oda.install": "Installer",
    "oda.use-detected": "Utiliser",
    "oda.open-page": "Page de téléchargement",
    "ollama.install": "Installer",
    "ollama.start": "Démarrer",
    "ollama.open-page": "Page de téléchargement",
    "model.pull": "Télécharger",
    "models.open": "Choisir un modèle",
    "streamdock.install-plugin": "Installer le plugin",
    "streamdock.install-autocad-plugin": "Installer le plugin",
    "streamdock.open-page": "Page de téléchargement",
    "autocad-plugin.open-page": "Page du projet",
}
UPDATE_LABEL = "Mettre à jour"
REINSTALL_LABEL = "Réinstaller"
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
    items = [
        _with_help(_oda_item(machine, system, oda_configured), PREREQUISITES_HELP),
        _with_help(_model_server_item(machine, system, assistant, server), PREREQUISITES_HELP),
        _with_help(
            _model_item(assistant, server, recommend(machine.memory_bytes)), PREREQUISITES_HELP
        ),
        _with_help(_stream_dock_item(machine, app_version), STREAM_DOCK_HELP),
        _with_help(_autocad_plugin_item(machine, autocad_plugin_latest), STREAM_DOCK_HELP),
    ]
    return SetupReport(system=system, items=items)


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
            detail=f"Installé mais pas configuré : {detected}",
            actions=_actions("oda.use-detected"),
        )
    return SetupItem(
        id="oda",
        label=label,
        status="missing",
        detail="Nécessaire pour lire les fichiers DWG.",
        actions=_oda_install_actions(machine),
    )


def _model_server_item(
    machine: Machine, system: SystemInfo, assistant: AssistantSettings, server: ModelServerState
) -> SetupItem:
    label = "Serveur du modèle local"
    if server.reachable:
        name = "Ollama" if server.is_ollama else "Serveur compatible OpenAI"
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
            detail="Ollama est installé mais ne répond pas.",
            actions=_actions("ollama.start"),
        )
    return SetupItem(
        id="model-server",
        label=label,
        status="missing",
        detail="Ollama fait tourner l'assistant sur ce poste, sans connexion externe.",
        actions=_ollama_install_actions(system),
    )


def _model_item(
    assistant: AssistantSettings, server: ModelServerState, recommended: str
) -> SetupItem:
    label = "Modèle d'IA"
    model = assistant.model
    if not server.reachable:
        return SetupItem(
            id="model",
            label=label,
            status="missing",
            detail=f"{model} — démarrez d'abord le serveur.",
        )
    if model in server.available:
        return SetupItem(id="model", label=label, status="ok", detail=f"{model} disponible.")
    if server.is_ollama:
        return SetupItem(
            id="model",
            label=label,
            status="missing",
            detail=f"{model} pas encore téléchargé. Recommandé pour ce poste : {recommended}.",
            actions=_actions("model.pull", "models.open"),
        )
    return SetupItem(
        id="model",
        label=label,
        status="missing",
        detail=f"{model} introuvable sur le serveur : chargez-le dans LM Studio ou changez de "
        "modèle.",
    )


def _stream_dock_item(machine: Machine, app_version: str | None) -> SetupItem:
    label = "Plugin Drawflow pour Stream Dock"
    if stream_dock_folder(machine) is None:
        return SetupItem(
            id="stream-dock",
            label=label,
            status="optional",
            detail="Logiciel Stream Dock (Mirabox) non installé.",
            actions=_actions("streamdock.open-page"),
        )
    if not stream_dock_plugin_installed(machine):
        return SetupItem(
            id="stream-dock",
            label=label,
            status="optional",
            detail="Pilotez Drawflow depuis les touches du Stream Dock.",
            actions=_actions("streamdock.install-plugin"),
        )
    installed = stream_dock_plugin_version(machine, DRAWFLOW_PLUGIN)
    return _installed_plugin_item(
        "stream-dock", label, "streamdock.install-plugin", installed, app_version
    )


def _autocad_plugin_item(machine: Machine, latest: str | None) -> SetupItem:
    label = "Plugin AutoCAD pour Stream Dock"
    if stream_dock_folder(machine) is None:
        return SetupItem(
            id="autocad-plugin",
            label=label,
            status="optional",
            detail="Logiciel Stream Dock (Mirabox) non installé.",
            actions=_actions("autocad-plugin.open-page"),
        )
    autocad = (
        "AutoCAD détecté."
        if find_autocad(machine) is not None
        else "AutoCAD (version complète, pas LT) non détecté sur ce poste."
    )
    if not stream_dock_plugin_installed(machine, AUTOCAD_PLUGIN):
        return SetupItem(
            id="autocad-plugin",
            label=label,
            status="optional",
            detail=f"Macros, calques et bascules AutoCAD depuis le Stream Dock. {autocad}",
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
    version = f"Version {installed} installée." if installed else "Installé."
    if available is not None and installed != available:
        return SetupItem(
            id=item_id,
            label=label,
            status="update",
            detail=f"{version} Version {available} disponible.",
            actions=[_action(install, UPDATE_LABEL)],
        )
    return SetupItem(
        id=item_id,
        label=label,
        status="ok",
        detail=f"{version} Redémarrez Stream Dock après chaque installation.",
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

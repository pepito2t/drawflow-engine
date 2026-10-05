"""Turns what is found on the computer into a checklist with the actions that fix each item."""

from dataclasses import dataclass
from pathlib import Path

from engine.assistant.catalog import recommend
from engine.core.settings_models import AssistantSettings
from engine.setup.locations import (
    find_oda,
    ollama_installed,
    stream_dock_folder,
    stream_dock_plugin_installed,
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
    "streamdock.open-page": "Page de téléchargement",
}
DOWNLOAD_PAGES: dict[ActionId, str] = {
    "oda.open-page": "https://www.opendesign.com/guestfiles/oda_file_converter",
    "ollama.open-page": "https://ollama.com/download",
    "streamdock.open-page": "https://mirabox.net/pages/download",
}
INSTALLABLE_WITH: dict[ActionId, set[PackageManager]] = {
    "ollama.install": {"winget", "brew"},
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
) -> SetupReport:
    system = SystemInfo(os=machine.os, arch=machine.arch, package_manager=_manager(machine))
    items = [
        _with_help(_oda_item(machine, system, oda_configured), PREREQUISITES_HELP),
        _with_help(_model_server_item(machine, system, assistant, server), PREREQUISITES_HELP),
        _with_help(
            _model_item(assistant, server, recommend(machine.memory_bytes)), PREREQUISITES_HELP
        ),
        _with_help(_stream_dock_item(machine), STREAM_DOCK_HELP),
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
        actions=_install_actions(system, "ollama.install", "ollama.open-page"),
    )


def _model_item(
    assistant: AssistantSettings, server: ModelServerState, recommended: str
) -> SetupItem:
    label = f"Modèle {assistant.model}"
    if not server.reachable:
        return SetupItem(
            id="model", label=label, status="missing", detail="Démarrez d'abord le serveur."
        )
    if assistant.model in server.available:
        return SetupItem(id="model", label=label, status="ok", detail="Disponible.")
    if server.is_ollama:
        return SetupItem(
            id="model",
            label=label,
            status="missing",
            detail=f"Pas encore téléchargé. Recommandé pour ce poste : {recommended}.",
            actions=_actions("model.pull", "models.open"),
        )
    return SetupItem(
        id="model",
        label=label,
        status="missing",
        detail="Introuvable sur le serveur : chargez-le dans LM Studio ou changez de modèle.",
    )


def _stream_dock_item(machine: Machine) -> SetupItem:
    label = "Plugin Stream Dock"
    if stream_dock_folder(machine) is None:
        return SetupItem(
            id="stream-dock",
            label=label,
            status="optional",
            detail="Facultatif : logiciel Stream Dock (Mirabox) non installé.",
            actions=_actions("streamdock.open-page"),
        )
    if stream_dock_plugin_installed(machine):
        return SetupItem(
            id="stream-dock",
            label=label,
            status="ok",
            detail="Installé. Réinstallez-le après une mise à jour de Drawflow.",
            actions=_actions("streamdock.install-plugin"),
        )
    return SetupItem(
        id="stream-dock",
        label=label,
        status="optional",
        detail="Pilotez Drawflow depuis les touches du Stream Dock.",
        actions=_actions("streamdock.install-plugin"),
    )


def _with_help(item: SetupItem, topic: str) -> SetupItem:
    return item.model_copy(update={"help": topic})


def _manager(machine: Machine) -> PackageManager | None:
    if machine.os == "windows" and machine.which("winget") is not None:
        return "winget"
    if machine.os == "macos" and machine.which("brew") is not None:
        return "brew"
    return None


def _install_actions(system: SystemInfo, install: ActionId, page: ActionId) -> list[SetupAction]:
    managers = INSTALLABLE_WITH.get(install, set())
    if system.package_manager is not None and system.package_manager in managers:
        return _actions(install, page)
    return _actions(page)


def _oda_install_actions(machine: Machine) -> list[SetupAction]:
    """ODA ships its own Windows installer; macOS has no silent install, only the page."""
    if machine.os == "windows":
        return _actions("oda.install", "oda.open-page")
    return _actions("oda.open-page")


def _actions(*ids: ActionId) -> list[SetupAction]:
    return [
        SetupAction(id=action, label=ACTION_LABELS[action], url=DOWNLOAD_PAGES.get(action))
        for action in ids
    ]

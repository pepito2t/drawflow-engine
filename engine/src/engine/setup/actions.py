"""The one-click fixes offered by the setup scan."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import anyio
import httpx

from engine.core.errors import EngineError, InvalidInputError
from engine.core.events import Emit, LogEvent, ProgressEvent, ResultEvent
from engine.core.registry import discover_modules
from engine.core.settings import load_assistant_settings, load_general_settings, save_settings
from engine.setup.commands import (
    CommandOutcome,
    CommandRunner,
    ProcessStarter,
    run_command,
    start_detached,
)
from engine.setup.locations import (
    OLLAMA_APP_MACOS,
    OLLAMA_PROGRAM,
    find_oda,
    stream_dock_plugins_folder,
)
from engine.setup.machine import LocalMachine, Machine
from engine.setup.oda_installer import install_oda
from engine.setup.ollama import START_WAIT_SECONDS, pull_model, wait_until_up
from engine.setup.report import ActionId
from engine.setup.stream_dock import install_plugin

OLLAMA_PACKAGE = "Ollama.Ollama"
OLLAMA_CASK = "ollama"
OLLAMA_APP_WINDOWS = Path("Programs") / "Ollama" / "ollama app.exe"
WINGET_FLAGS = (
    "--exact",
    "--silent",
    "--accept-package-agreements",
    "--accept-source-agreements",
    "--disable-interactivity",
)
# winget reports "already installed" and "no newer version" as failures; both mean done.
WINGET_ALREADY_DONE = {0x8A150061, 0x8A15002B}
UNSIGNED_32_BITS = 0xFFFFFFFF
# 0x8019xxxx: the download got an HTTP error (xxxx = status), e.g. a file removed upstream.
HTTP_ERROR_FACILITY = 0x80190000
FACILITY_MASK = 0xFFFF0000
STATUS_MASK = 0x0000FFFF
PERCENT = 100


class SetupError(EngineError):
    pass


@dataclass(frozen=True)
class SetupContext:
    settings: Path
    emit: Emit
    machine: Machine = field(default_factory=LocalMachine)
    run: CommandRunner = run_command
    start: ProcessStarter = start_detached
    transport: httpx.AsyncBaseTransport | None = None
    start_wait_seconds: float = START_WAIT_SECONDS
    app_version: str | None = None


def run_action(action: str, context: SetupContext) -> None:
    handlers: dict[ActionId, Callable[[SetupContext], str]] = {
        "oda.install": _install_oda,
        "oda.use-detected": _use_detected_oda,
        "ollama.install": _install_ollama,
        "ollama.start": _start_ollama,
        "model.pull": _pull_model,
        "streamdock.install-plugin": _install_stream_dock_plugin,
    }
    if action not in handlers:
        raise InvalidInputError(f"Action d'installation inconnue : {action}.")
    summary = handlers[action](context)
    context.emit(ResultEvent(summary=summary))


def _install_oda(context: SetupContext) -> str:
    if context.machine.os != "windows":
        raise SetupError(
            "L'installation automatique d'ODA File Converter n'existe que sous Windows.",
            hint="Utilisez la page de téléchargement.",
        )
    context.emit(LogEvent(message="Téléchargement d'ODA File Converter depuis le site officiel…"))

    def on_download(percent: int) -> None:
        context.emit(ProgressEvent(current=percent, total=PERCENT, message="Téléchargement d'ODA"))

    install_oda(context.run, on_download, context.transport)
    return _use_detected_oda(context)


def _use_detected_oda(context: SetupContext) -> str:
    detected = find_oda(context.machine)
    if detected is None:
        raise SetupError(
            "ODA File Converter est introuvable dans les dossiers d'installation habituels.",
            hint="Indiquez le chemin de ODAFileConverter.exe dans Paramètres → Général.",
        )
    general = load_general_settings(context.settings).model_dump(mode="json")
    general["oda_converter_path"] = str(detected)
    save_settings(context.settings, {"general": general}, discover_modules())
    return f"ODA File Converter configuré : {detected}"


def _install_ollama(context: SetupContext) -> str:
    if context.machine.os == "windows":
        _winget_install(context, OLLAMA_PACKAGE, "Ollama")
    else:
        context.emit(LogEvent(message="Installation d'Ollama avec Homebrew…"))
        _check(context.run(["brew", "install", "--cask", OLLAMA_CASK]), "Ollama")
    return _start_ollama(context)


def _start_ollama(context: SetupContext) -> str:
    context.emit(LogEvent(message="Démarrage d'Ollama…"))
    context.start(_ollama_launcher(context.machine))
    url = load_assistant_settings(context.settings).model_server_url
    if not anyio.run(wait_until_up, url, context.transport, context.start_wait_seconds):
        raise SetupError(
            "Ollama ne répond pas après son démarrage.",
            hint="Lancez Ollama depuis le menu Démarrer, puis analysez à nouveau.",
        )
    return "Ollama est démarré."


def _pull_model(context: SetupContext) -> str:
    assistant = load_assistant_settings(context.settings)

    def on_percent(percent: int, status: str) -> None:
        context.emit(ProgressEvent(current=percent, total=PERCENT, message=status))

    anyio.run(
        pull_model, assistant.model_server_url, assistant.model, on_percent, context.transport
    )
    return f"Modèle {assistant.model} téléchargé."


def _install_stream_dock_plugin(context: SetupContext) -> str:
    plugins = stream_dock_plugins_folder(context.machine)
    if plugins is None:
        raise SetupError(
            "Le logiciel Stream Dock est introuvable sur ce poste.",
            hint="Installez Stream Dock depuis la page de téléchargement de Mirabox.",
        )
    if context.app_version is None:
        raise SetupError("Version de Drawflow inconnue : relancez l'installation depuis l'app.")
    context.emit(LogEvent(message="Téléchargement du plugin Stream Dock…"))
    return install_plugin(plugins, context.app_version, context.transport)


def _ollama_launcher(machine: Machine) -> list[str]:
    if machine.os == "macos" and machine.is_dir(OLLAMA_APP_MACOS):
        return ["open", "-a", str(OLLAMA_APP_MACOS)]
    local = machine.folder("LOCALAPPDATA")
    if (
        machine.os == "windows"
        and local is not None
        and machine.is_file(local / OLLAMA_APP_WINDOWS)
    ):
        return [str(local / OLLAMA_APP_WINDOWS)]
    program = machine.which(OLLAMA_PROGRAM)
    if program is None:
        raise SetupError("Ollama n'est pas installé.", hint="Utilisez le bouton Installer.")
    return [str(program), "serve"]


def _winget_install(context: SetupContext, package: str, name: str) -> None:
    if context.machine.which("winget") is None:
        raise SetupError(
            "winget n'est pas disponible sur ce poste.",
            hint="Utilisez la page de téléchargement, ou mettez Windows à jour.",
        )
    context.emit(LogEvent(message=f"Installation de {name} avec winget (plusieurs minutes)…"))
    context.emit(ProgressEvent(current=0, total=PERCENT, message=f"Installation de {name}"))
    _check(context.run(["winget", "install", "--id", package, *WINGET_FLAGS]), name)


def _check(outcome: CommandOutcome, name: str) -> None:
    code = outcome.return_code & UNSIGNED_32_BITS
    if code == 0 or code in WINGET_ALREADY_DONE:
        return
    if code & FACILITY_MASK == HTTP_ERROR_FACILITY:
        raise SetupError(
            f"Le téléchargement de {name} a échoué : le fichier proposé par winget n'est plus "
            f"disponible chez l'éditeur (HTTP {code & STATUS_MASK}).",
            hint=f"Cliquez sur « Page de téléchargement », installez {name}, puis sur "
            "« Analyser à nouveau » : Drawflow le détectera.",
        )
    raise SetupError(
        f"L'installation de {name} a échoué (code {outcome.return_code}).",
        hint=outcome.tail() or "Réessayez, ou utilisez la page de téléchargement.",
    )

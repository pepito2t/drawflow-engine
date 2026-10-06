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
from engine.setup.installer_download import DownloadProgress
from engine.setup.locations import (
    AUTOCAD_PLUGIN,
    DRAWFLOW_PLUGIN,
    OLLAMA_APP_MACOS,
    OLLAMA_PROGRAM,
    find_oda,
    stream_dock_plugins_folder,
)
from engine.setup.machine import LocalMachine, Machine
from engine.setup.messages import t
from engine.setup.oda_installer import install_oda
from engine.setup.ollama import START_WAIT_SECONDS, pull_model, wait_until_up
from engine.setup.ollama_installer import install_ollama_windows
from engine.setup.report import ActionId
from engine.setup.stream_dock import (
    AUTOCAD_PLUGIN_ASSET_URL,
    DRAWFLOW_PLUGIN_ASSET_URL,
    install_plugin,
)

OLLAMA_CASK = "ollama"
OLLAMA_APP_WINDOWS = Path("Programs") / "Ollama" / "ollama app.exe"
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
        "streamdock.install-autocad-plugin": _install_autocad_plugin,
    }
    if action not in handlers:
        raise InvalidInputError(t("actions.unknown", action=action))
    summary = handlers[action](context)
    context.emit(ResultEvent(summary=summary))


def _install_oda(context: SetupContext) -> str:
    if context.machine.os != "windows":
        raise SetupError(t("actions.oda_windows_only"), hint=t("actions.oda_windows_only.hint"))
    context.emit(LogEvent(message=t("actions.oda_downloading")))
    install_oda(context.run, _download_progress(context, "ODA File Converter"), context.transport)
    return _use_detected_oda(context)


def _use_detected_oda(context: SetupContext) -> str:
    detected = find_oda(context.machine)
    if detected is None:
        raise SetupError(t("actions.oda_not_found"), hint=t("actions.oda_not_found.hint"))
    general = load_general_settings(context.settings).model_dump(mode="json")
    general["oda_converter_path"] = str(detected)
    save_settings(context.settings, {"general": general}, discover_modules())
    return t("actions.oda_configured", path=detected)


def _install_ollama(context: SetupContext) -> str:
    if context.machine.os == "windows":
        context.emit(LogEvent(message=t("actions.ollama_downloading")))
        install_ollama_windows(
            context.run, _download_progress(context, "Ollama"), context.transport
        )
    else:
        context.emit(LogEvent(message=t("actions.ollama_brew")))
        _check(context.run(["brew", "install", "--cask", OLLAMA_CASK]), "Ollama")
    return _start_ollama(context)


def _start_ollama(context: SetupContext) -> str:
    context.emit(LogEvent(message=t("actions.ollama_starting")))
    context.start(_ollama_launcher(context.machine))
    url = load_assistant_settings(context.settings).model_server_url
    if not anyio.run(wait_until_up, url, context.transport, context.start_wait_seconds):
        raise SetupError(t("actions.ollama_not_up"), hint=t("actions.ollama_not_up.hint"))
    return t("actions.ollama_started")


def _pull_model(context: SetupContext) -> str:
    assistant = load_assistant_settings(context.settings)

    def on_percent(percent: int, status: str) -> None:
        context.emit(ProgressEvent(current=percent, total=PERCENT, message=status))

    anyio.run(
        pull_model, assistant.model_server_url, assistant.model, on_percent, context.transport
    )
    return t("actions.model_downloaded", model=assistant.model)


def _install_stream_dock_plugin(context: SetupContext) -> str:
    plugins = _stream_dock_plugins(context)
    if context.app_version is None:
        raise SetupError(t("actions.app_version_unknown"))
    context.emit(LogEvent(message=t("actions.plugin_downloading")))
    asset_url = DRAWFLOW_PLUGIN_ASSET_URL.format(version=context.app_version)
    return install_plugin(plugins, DRAWFLOW_PLUGIN, asset_url, context.transport)


def _install_autocad_plugin(context: SetupContext) -> str:
    plugins = _stream_dock_plugins(context)
    context.emit(LogEvent(message=t("actions.autocad_plugin_downloading")))
    return install_plugin(plugins, AUTOCAD_PLUGIN, AUTOCAD_PLUGIN_ASSET_URL, context.transport)


def _stream_dock_plugins(context: SetupContext) -> Path:
    plugins = stream_dock_plugins_folder(context.machine)
    if plugins is None:
        raise SetupError(
            t("actions.stream_dock_not_found"), hint=t("actions.stream_dock_not_found.hint")
        )
    return plugins


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
        raise SetupError(
            t("actions.ollama_not_installed"), hint=t("actions.ollama_not_installed.hint")
        )
    return [str(program), "serve"]


def _download_progress(context: SetupContext, name: str) -> DownloadProgress:
    def on_percent(percent: int) -> None:
        key = "actions.downloading" if percent < PERCENT else "actions.installing"
        context.emit(ProgressEvent(current=percent, total=PERCENT, message=t(key, name=name)))

    return on_percent


def _check(outcome: CommandOutcome, name: str) -> None:
    if outcome.return_code == 0:
        return
    raise SetupError(
        t("actions.install_failed", name=name, code=outcome.return_code),
        hint=outcome.tail() or t("actions.retry_or_page"),
    )

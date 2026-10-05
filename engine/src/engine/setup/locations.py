"""Standard install locations of the third-party tools Drawflow relies on."""

import json
from pathlib import Path

from engine.setup.machine import Machine

ODA_EXECUTABLE_WINDOWS = "ODAFileConverter.exe"
ODA_APP_MACOS = Path("/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter")
OLLAMA_PROGRAM = "ollama"
OLLAMA_WINDOWS = Path("Programs") / "Ollama" / "ollama.exe"
OLLAMA_APP_MACOS = Path("/Applications/Ollama.app")
STREAM_DOCK_FOLDER_WINDOWS = Path("HotSpot") / "StreamDock"
STREAM_DOCK_PLUGINS = "plugins"
DRAWFLOW_PLUGIN = "ch.drawflow.sdPlugin"
AUTOCAD_PLUGIN = "com.tmbk.streamdock.autocad.sdPlugin"
PLUGIN_MANIFEST = "manifest.json"
AUTOCAD_EXECUTABLE = "acad.exe"
AUTODESK_FOLDER = "Autodesk"


def find_oda(machine: Machine) -> Path | None:
    if machine.os == "macos":
        return ODA_APP_MACOS if machine.is_file(ODA_APP_MACOS) else None
    candidates: list[Path] = []
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        root = machine.folder(variable)
        if root is not None:
            candidates += machine.glob(root / "ODA", f"*/{ODA_EXECUTABLE_WINDOWS}")
    # Folders are named after the version: the last one sorted is the most recent.
    return candidates[-1] if candidates else None


def ollama_installed(machine: Machine) -> bool:
    if machine.which(OLLAMA_PROGRAM) is not None:
        return True
    if machine.os == "macos":
        return machine.is_dir(OLLAMA_APP_MACOS)
    local = machine.folder("LOCALAPPDATA")
    return local is not None and machine.is_file(local / OLLAMA_WINDOWS)


def stream_dock_folder(machine: Machine) -> Path | None:
    """Stream Dock keeps its settings and plugins in %APPDATA%; only Windows is supported."""
    roaming = machine.folder("APPDATA") if machine.os == "windows" else None
    if roaming is None or not machine.is_dir(roaming / STREAM_DOCK_FOLDER_WINDOWS):
        return None
    return roaming / STREAM_DOCK_FOLDER_WINDOWS


def stream_dock_plugins_folder(machine: Machine) -> Path | None:
    folder = stream_dock_folder(machine)
    return None if folder is None else folder / STREAM_DOCK_PLUGINS


def stream_dock_plugin_installed(machine: Machine, plugin_id: str = DRAWFLOW_PLUGIN) -> bool:
    plugins = stream_dock_plugins_folder(machine)
    return plugins is not None and machine.is_dir(plugins / plugin_id)


def stream_dock_plugin_version(machine: Machine, plugin_id: str) -> str | None:
    plugins = stream_dock_plugins_folder(machine)
    if plugins is None:
        return None
    manifest = machine.read_text(plugins / plugin_id / PLUGIN_MANIFEST)
    if manifest is None:
        return None
    try:
        version = json.loads(manifest).get("Version")
    except (ValueError, AttributeError):
        return None
    return str(version) if version else None


def find_autocad(machine: Machine) -> Path | None:
    """Full AutoCAD only: LT ships acadlt.exe and exposes no COM automation."""
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        root = machine.folder(variable)
        if root is None:
            continue
        found = machine.glob(root / AUTODESK_FOLDER, f"AutoCAD */{AUTOCAD_EXECUTABLE}")
        executables = [path for path in found if path.name.lower() == AUTOCAD_EXECUTABLE]
        if executables:
            return executables[-1]
    return None

"""Standard install locations of the third-party tools Drawflow relies on."""

from pathlib import Path

from engine.setup.machine import Machine

ODA_EXECUTABLE_WINDOWS = "ODAFileConverter.exe"
ODA_APP_MACOS = Path("/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter")
OLLAMA_PROGRAM = "ollama"
OLLAMA_WINDOWS = Path("Programs") / "Ollama" / "ollama.exe"
OLLAMA_APP_MACOS = Path("/Applications/Ollama.app")
STREAM_DECK_WINDOWS = Path("Elgato") / "StreamDeck" / "StreamDeck.exe"
STREAM_DECK_APP_MACOS = Path("/Applications/Elgato Stream Deck.app")
STREAM_DECK_PLUGIN = "ch.drawflow.sdPlugin"
STREAM_DECK_PLUGINS_WINDOWS = Path("Elgato") / "StreamDeck" / "Plugins"
STREAM_DECK_PLUGINS_MACOS = Path("Library/Application Support/com.elgato.StreamDeck/Plugins")


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


def stream_deck_installed(machine: Machine) -> bool:
    if machine.os == "macos":
        return machine.is_dir(STREAM_DECK_APP_MACOS)
    root = machine.folder("ProgramFiles")
    return root is not None and machine.is_file(root / STREAM_DECK_WINDOWS)


def stream_deck_plugin_installed(machine: Machine) -> bool:
    if machine.os == "macos":
        plugins = machine.home / STREAM_DECK_PLUGINS_MACOS
    else:
        roaming = machine.folder("APPDATA")
        if roaming is None:
            return False
        plugins = roaming / STREAM_DECK_PLUGINS_WINDOWS
    return machine.is_dir(plugins / STREAM_DECK_PLUGIN)

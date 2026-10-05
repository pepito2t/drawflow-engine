"""Installs Ollama on Windows from ollama.com: winget shows no progress on a 1.5 GB download."""

import tempfile
from pathlib import Path

import anyio
import httpx

from engine.core.errors import EngineError
from engine.setup.commands import CommandOutcome, CommandRunner
from engine.setup.installer_download import DownloadProgress, download_installer

OLLAMA_SETUP_URL = "https://ollama.com/download/OllamaSetup.exe"
OLLAMA_NAME = "Ollama"
OLLAMA_SETUP_NAME = "OllamaSetup.exe"
MAX_SETUP_BYTES = 4_000_000_000
# Inno Setup: per-user install, no window, no reboot prompt.
SILENT_FLAGS = ("/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES")
SETUP_SUCCESS = 0


class OllamaInstallError(EngineError):
    pass


def install_ollama_windows(
    run: CommandRunner,
    on_progress: DownloadProgress,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    with tempfile.TemporaryDirectory(prefix="drawflow-ollama-") as folder:
        setup = Path(folder) / OLLAMA_SETUP_NAME
        anyio.run(_download, setup, on_progress, transport)
        _check(run([str(setup), *SILENT_FLAGS]))


async def _download(
    target: Path, on_progress: DownloadProgress, transport: httpx.AsyncBaseTransport | None
) -> None:
    await download_installer(
        OLLAMA_SETUP_URL,
        target,
        name=OLLAMA_NAME,
        max_bytes=MAX_SETUP_BYTES,
        on_progress=on_progress,
        transport=transport,
    )


def _check(outcome: CommandOutcome) -> None:
    if outcome.return_code != SETUP_SUCCESS:
        raise OllamaInstallError(
            f"L'installation d'Ollama a échoué (code {outcome.return_code}).",
            hint=outcome.tail() or "Réessayez, ou utilisez la page de téléchargement.",
        )

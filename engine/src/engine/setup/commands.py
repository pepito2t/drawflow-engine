"""Runs installers as argument lists (never through a shell)."""

import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

# Downloading and installing a package can take several minutes on a slow connection.
INSTALL_TIMEOUT_SECONDS = 15 * 60
WINDOWS_NO_WINDOW_FLAG = 0x08000000
OUTPUT_TAIL_LINES = 5


@dataclass(frozen=True)
class CommandOutcome:
    return_code: int
    output: str

    def tail(self) -> str:
        lines = [line.strip() for line in self.output.splitlines() if line.strip()]
        return "\n".join(lines[-OUTPUT_TAIL_LINES:])


CommandRunner = Callable[[Sequence[str]], CommandOutcome]
ProcessStarter = Callable[[Sequence[str]], None]


def run_command(arguments: Sequence[str]) -> CommandOutcome:
    completed = subprocess.run(
        list(arguments),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=INSTALL_TIMEOUT_SECONDS,
        creationflags=_no_window(),
        check=False,
    )
    return CommandOutcome(completed.returncode, completed.stdout + completed.stderr)


def start_detached(arguments: Sequence[str]) -> None:
    """Starts a background program that must outlive the engine (the Ollama server)."""
    subprocess.Popen(
        list(arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_no_window() | _detached(),
        start_new_session=sys.platform != "win32",
    )


def _no_window() -> int:
    return WINDOWS_NO_WINDOW_FLAG if sys.platform == "win32" else 0


def _detached() -> int:
    return int(getattr(subprocess, "DETACHED_PROCESS", 0))

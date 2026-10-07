"""Runs installers as argument lists (never through a shell)."""

import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from engine.setup.errors import SetupError
from engine.setup.messages import t

# Downloading and installing a package can take several minutes on a slow connection.
INSTALL_TIMEOUT_SECONDS = 15 * 60
WINDOWS_NO_WINDOW_FLAG = 0x08000000
# Console programs such as winget write in the console code page, not in UTF-8.
WINDOWS_CONSOLE_ENCODING = "oem"
OUTPUT_TAIL_LINES = 5
SECONDS_PER_MINUTE = 60


@dataclass(frozen=True)
class CommandOutcome:
    return_code: int
    output: str

    def tail(self) -> str:
        lines = [line.strip() for line in self.output.splitlines() if line.strip()]
        return "\n".join(lines[-OUTPUT_TAIL_LINES:])


CommandRunner = Callable[[Sequence[str]], CommandOutcome]
ProcessStarter = Callable[[Sequence[str]], None]


def run_command(
    arguments: Sequence[str], timeout_seconds: float = INSTALL_TIMEOUT_SECONDS
) -> CommandOutcome:
    try:
        completed = subprocess.run(
            list(arguments),
            capture_output=True,
            text=True,
            encoding=WINDOWS_CONSOLE_ENCODING if sys.platform == "win32" else "utf-8",
            errors="replace",
            timeout=timeout_seconds,
            creationflags=_no_window(),
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        minutes = max(1, round(timeout_seconds / SECONDS_PER_MINUTE))
        raise SetupError(
            t("commands.timeout", program=_program(arguments), minutes=minutes),
            hint=t("commands.timeout.hint"),
        ) from error
    except OSError as error:
        raise _start_failed(arguments) from error
    return CommandOutcome(completed.returncode, completed.stdout + completed.stderr)


def start_detached(arguments: Sequence[str]) -> None:
    """Starts a background program that must outlive the engine (the Ollama server)."""
    try:
        subprocess.Popen(
            list(arguments),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window() | _detached(),
            start_new_session=sys.platform != "win32",
        )
    except OSError as error:
        raise _start_failed(arguments) from error


def _start_failed(arguments: Sequence[str]) -> SetupError:
    message = t("commands.start_failed", program=_program(arguments))
    return SetupError(message, hint=t("commands.start_failed.hint"))


def _program(arguments: Sequence[str]) -> str:
    return Path(arguments[0]).name if arguments else ""


def _no_window() -> int:
    return WINDOWS_NO_WINDOW_FLAG if sys.platform == "win32" else 0


def _detached() -> int:
    return int(getattr(subprocess, "DETACHED_PROCESS", 0))

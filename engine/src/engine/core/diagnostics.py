"""Keeps the real cause of every failure on disk, so a user can send it when something breaks."""

import json
import locale
import subprocess
import traceback
from datetime import UTC, datetime
from pathlib import Path

from engine.core.errors import EngineError

LOGS_FOLDER = "logs"
LOG_FILE = "engine.log"
ROTATED_SUFFIX = ".1"
MAX_LOG_BYTES = 1_000_000
CAUSE_MAX_LENGTH = 2_000
PROCESS_OUTPUT_MAX_LENGTH = 500


def log_file(settings: Path | None) -> Path | None:
    return None if settings is None else settings.parent / LOGS_FOLDER / LOG_FILE


def record_failure(settings: Path | None, command: list[str], error: BaseException) -> None:
    """Never raises: a failure to log must not hide the failure being logged."""
    path = log_file(settings)
    if path is None:
        return
    entry = {
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "command": command,
        "type": type(error).__name__,
        "message": _message(error),
        "hint": error.hint if isinstance(error, EngineError) else None,
        "file": str(error.file) if isinstance(error, EngineError) and error.file else None,
        "cause": _cause(error),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _rotate(path)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        return


def _message(error: BaseException) -> str:
    return error.message if isinstance(error, EngineError) else str(error)


def _cause(error: BaseException) -> str:
    """The chain under the readable message: HTTP bodies, OS errors, tracebacks."""
    if isinstance(error, EngineError):
        cause = error.__cause__
        text = "" if cause is None else _describe(cause)
    else:
        text = "".join(traceback.format_exception(error))
    return text.strip()[:CAUSE_MAX_LENGTH]


def _describe(cause: BaseException) -> str:
    text = f"{type(cause).__name__}: {cause}"
    if isinstance(cause, subprocess.CalledProcessError):
        # Its str() only says the exit status; what the program printed is the actual reason.
        text += _process_output(cause)
    return text


def _process_output(error: subprocess.CalledProcessError) -> str:
    streams = (("stdout", error.output), ("stderr", error.stderr))
    return "".join(
        f"\n{label}: {_as_text(output)[:PROCESS_OUTPUT_MAX_LENGTH]}"
        for label, output in streams
        if _as_text(output)
    )


def _as_text(output: object) -> str:
    if isinstance(output, bytes):
        return _decode(output).strip()
    return str(output).strip() if output else ""


def _decode(output: bytes) -> str:
    # Windows programs such as ODA write in the system code page, not in UTF-8.
    try:
        return output.decode("utf-8")
    except UnicodeDecodeError:
        return output.decode(locale.getpreferredencoding(False), errors="replace")


def _rotate(path: Path) -> None:
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return
    if size >= MAX_LOG_BYTES:
        path.replace(path.with_name(f"{path.name}{ROTATED_SUFFIX}"))

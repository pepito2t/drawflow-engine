import json
import os
import time
import uuid
from pathlib import Path
from typing import TextIO

from engine.core.paths import extended_path

TEMPORARY_SUFFIX = ".tmp"
# Windows refuses to replace a file another process is replacing at that instant.
REPLACE_ATTEMPTS = 5
REPLACE_RETRY_SECONDS = 0.02


def write_json_atomically(path: Path, payload: object, *, mode: int | None = None) -> None:
    """A crash mid-write leaves the previous file intact. Raises OSError for the caller to word.

    With `mode`, the file is born with those permissions: it is never readable more widely.
    """
    temporary = temporary_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _open_for_writing(temporary, mode) as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2))
            stream.flush()
            os.fsync(stream.fileno())
        replace_file(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _open_for_writing(path: Path, mode: int | None) -> TextIO:
    if mode is None:
        return path.open("w", encoding="utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    return os.fdopen(descriptor, "w", encoding="utf-8")


def temporary_path(path: Path) -> Path:
    # One name per call: two processes may save the same file at the same time.
    return path.with_name(f"{path.name}.{os.getpid()}-{uuid.uuid4().hex}{TEMPORARY_SUFFIX}")


def replace_file(temporary: Path, path: Path) -> None:
    """Moves `temporary` over `path`, waiting out a Windows lock held by another process."""
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            extended_path(temporary).replace(extended_path(path))
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(REPLACE_RETRY_SECONDS)

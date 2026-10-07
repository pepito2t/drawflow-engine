import json
import os
import time
import uuid
from pathlib import Path

TEMPORARY_SUFFIX = ".tmp"
# Windows refuses to replace a file another process is replacing at that instant.
REPLACE_ATTEMPTS = 5
REPLACE_RETRY_SECONDS = 0.02


def write_json_atomically(path: Path, payload: object) -> None:
    """A crash mid-write leaves the previous file intact. Raises OSError for the caller to word."""
    temporary = temporary_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2))
            stream.flush()
            os.fsync(stream.fileno())
        _replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def temporary_path(path: Path) -> Path:
    # One name per call: two processes may save the same file at the same time.
    return path.with_name(f"{path.name}.{os.getpid()}-{uuid.uuid4().hex}{TEMPORARY_SUFFIX}")


def _replace(temporary: Path, path: Path) -> None:
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(REPLACE_RETRY_SECONDS)

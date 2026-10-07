import json
import os
import uuid
from pathlib import Path

TEMPORARY_SUFFIX = ".tmp"


def write_json_atomically(path: Path, payload: object) -> None:
    """A crash mid-write leaves the previous file intact. Raises OSError for the caller to word."""
    temporary = temporary_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2))
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def temporary_path(path: Path) -> Path:
    # One name per call: two processes may save the same file at the same time.
    return path.with_name(f"{path.name}.{os.getpid()}-{uuid.uuid4().hex}{TEMPORARY_SUFFIX}")

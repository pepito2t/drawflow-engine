import json
from pathlib import Path

TEMPORARY_SUFFIX = ".tmp"


def write_json_atomically(path: Path, payload: object) -> None:
    """A crash mid-write leaves the previous file intact. Raises OSError for the caller to word."""
    temporary = path.with_name(f"{path.name}{TEMPORARY_SUFFIX}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)

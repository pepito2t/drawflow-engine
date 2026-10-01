from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from engine.core.cache import file_digest


@dataclass(frozen=True)
class Duplicate:
    path: Path
    same_as: Path


@dataclass(frozen=True)
class Deduplicated:
    unique: list[Path] = field(default_factory=list)
    duplicates: list[Duplicate] = field(default_factory=list)


def deduplicate(paths: Sequence[Path], digest: Callable[[Path], str] = file_digest) -> Deduplicated:
    """Keeps the first file of each identical content, wherever it sits."""
    first_by_digest: dict[str, Path] = {}
    result = Deduplicated()
    for path in paths:
        key = digest(path)
        if key in first_by_digest:
            result.duplicates.append(Duplicate(path=path, same_as=first_by_digest[key]))
        else:
            first_by_digest[key] = path
            result.unique.append(path)
    return result

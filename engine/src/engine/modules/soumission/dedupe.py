from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Duplicate:
    path: Path
    same_as: Path


@dataclass(frozen=True)
class Deduplicated:
    unique: list[Path] = field(default_factory=list)
    duplicates: list[Duplicate] = field(default_factory=list)


def deduplicate(digests: Sequence[tuple[Path, str]]) -> Deduplicated:
    """Keeps the first file of each identical content, wherever it sits."""
    first_by_digest: dict[str, Path] = {}
    result = Deduplicated()
    for path, digest in digests:
        if digest in first_by_digest:
            result.duplicates.append(Duplicate(path=path, same_as=first_by_digest[digest]))
        else:
            first_by_digest[digest] = path
            result.unique.append(path)
    return result

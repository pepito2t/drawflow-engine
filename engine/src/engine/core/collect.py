from collections.abc import Collection, Sequence
from pathlib import Path

from engine.core.errors import EngineError
from engine.core.events import Emit, LogEvent, WarningEvent
from engine.core.messages import t


class FileCollectionError(EngineError):
    pass


def collect_files(
    files: Sequence[Path],
    folders: Sequence[Path],
    *,
    suffixes: Collection[str],
    kind: str,
    recursive: bool,
    emit: Emit,
) -> list[Path]:
    """Gathers matching files from explicit paths and folders, without duplicates."""
    found: dict[Path, Path] = {}
    for file in files:
        if not has_suffix(file, suffixes):
            emit(WarningEvent(message=t("collect.ignored", kind=kind), file=str(file)))
        elif not file.is_file():
            emit(
                WarningEvent(
                    message=t("collect.missing"), file=str(file), hint=t("collect.missing_hint")
                )
            )
        else:
            found.setdefault(file.resolve(), file)
    for folder in folders:
        for path in _files_in(folder, suffixes, recursive=recursive):
            found.setdefault(path.resolve(), path)
    if not found:
        raise FileCollectionError(
            t("collect.none_found", kind=kind), hint=t("collect.none_found_hint")
        )
    ordered = sorted(found.values(), key=lambda path: str(path).casefold())
    emit(LogEvent(message=t("collect.count", count=len(ordered))))
    return ordered


def has_suffix(path: Path, suffixes: Collection[str]) -> bool:
    return path.suffix.lower() in suffixes


def _files_in(folder: Path, suffixes: Collection[str], *, recursive: bool) -> list[Path]:
    if not folder.is_dir():
        raise FileCollectionError(t("collect.folder_missing"), file=folder)
    candidates = folder.rglob("*") if recursive else folder.glob("*")
    return [path for path in candidates if path.is_file() and has_suffix(path, suffixes)]

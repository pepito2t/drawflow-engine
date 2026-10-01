from collections.abc import Collection, Sequence
from pathlib import Path

from engine.core.errors import EngineError
from engine.core.events import Emit, LogEvent, WarningEvent


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
        if has_suffix(file, suffixes):
            found.setdefault(file.resolve(), file)
        else:
            emit(WarningEvent(message=f"Fichier ignoré : ce n'est pas un {kind}.", file=str(file)))
    for folder in folders:
        for path in _files_in(folder, suffixes, recursive=recursive):
            found.setdefault(path.resolve(), path)
    if not found:
        raise FileCollectionError(
            f"Aucun fichier {kind} trouvé.",
            hint="Vérifiez les fichiers et dossiers choisis (et l'option sous-dossiers).",
        )
    ordered = sorted(found.values(), key=lambda path: str(path).casefold())
    emit(LogEvent(message=f"{len(ordered)} fichier(s) à traiter."))
    return ordered


def has_suffix(path: Path, suffixes: Collection[str]) -> bool:
    return path.suffix.lower() in suffixes


def _files_in(folder: Path, suffixes: Collection[str], *, recursive: bool) -> list[Path]:
    if not folder.is_dir():
        raise FileCollectionError("Dossier introuvable.", file=folder)
    candidates = folder.rglob("*") if recursive else folder.glob("*")
    return [path for path in candidates if path.is_file() and has_suffix(path, suffixes)]

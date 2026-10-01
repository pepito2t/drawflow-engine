import hashlib
import os
import sys
from collections.abc import Callable
from pathlib import Path

from engine.core.errors import EngineError
from engine.core.events import Emit, WarningEvent
from engine.core.settings_models import GeneralSettings

APP_FOLDER_NAME = "drawflow"
HASH_CHUNK_BYTES = 1024 * 1024
SHARD_LENGTH = 2
TEMPORARY_SUFFIX = ".partial"

Producer = Callable[[Path, Path], None]


class CacheError(EngineError):
    pass


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def default_cache_root() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / APP_FOLDER_NAME / "cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / APP_FOLDER_NAME
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / APP_FOLDER_NAME


def resolve_cache_root(general: GeneralSettings) -> Path:
    return general.cache_folder or default_cache_root()


class FileCache:
    """Stores derived files keyed by the SHA-256 of their source content."""

    def __init__(self, root: Path, namespace: str) -> None:
        self._folder = root / namespace

    def entry_path(self, digest: str, suffix: str) -> Path:
        return self._folder / digest[:SHARD_LENGTH] / f"{digest}{suffix}"

    def get_or_create(self, source: Path, suffix: str, produce: Producer, emit: Emit) -> Path:
        entry = self.entry_path(file_digest(source), suffix)
        if self._is_usable(entry, source, emit):
            return entry
        self._prepare_folder(entry.parent)
        temporary = entry.with_name(entry.name + TEMPORARY_SUFFIX)
        produce(source, temporary)
        temporary.replace(entry)
        return entry

    def _is_usable(self, entry: Path, source: Path, emit: Emit) -> bool:
        try:
            size = entry.stat().st_size
        except FileNotFoundError:
            return False
        except OSError:
            size = 0
        if size > 0:
            return True
        emit(WarningEvent(message="Entrée de cache invalide, nouveau calcul.", file=str(source)))
        return False

    def _prepare_folder(self, folder: Path) -> None:
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise CacheError(
                "Le dossier de cache est inaccessible.",
                file=folder,
                hint="Choisissez un autre dossier de cache dans Paramètres.",
            ) from error

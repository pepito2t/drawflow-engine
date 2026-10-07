import hashlib
import os
import sys
import uuid
from collections.abc import Callable
from pathlib import Path

from engine.core.errors import EngineError
from engine.core.events import Emit, WarningEvent
from engine.core.messages import t
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

    def has(self, source: Path, suffix: str) -> bool:
        """Whether a usable entry already exists, without producing anything."""
        try:
            return self.entry_path(file_digest(source), suffix).stat().st_size > 0
        except OSError:
            return False

    def get_or_create(self, source: Path, suffix: str, produce: Producer, emit: Emit) -> Path:
        entry = self.entry_path(file_digest(source), suffix)
        if self._is_usable(entry, source, emit):
            return entry
        self._prepare_folder(entry.parent)
        temporary = self._temporary_path(entry)
        try:
            produce(source, temporary)
            self._promote(temporary, entry, source, emit)
        finally:
            temporary.unlink(missing_ok=True)
        return entry

    def _temporary_path(self, entry: Path) -> Path:
        # One name per call: parallel workers may convert identical files at the same time.
        return entry.with_name(f"{entry.name}.{os.getpid()}-{uuid.uuid4().hex}{TEMPORARY_SUFFIX}")

    def _promote(self, temporary: Path, entry: Path, source: Path, emit: Emit) -> None:
        if self._is_usable(entry, source, emit):
            return
        try:
            temporary.replace(entry)
        except PermissionError:
            # Windows refuses to replace a file another worker is already reading.
            if not self._is_usable(entry, source, emit):
                raise

    def _is_usable(self, entry: Path, source: Path, emit: Emit) -> bool:
        try:
            size = entry.stat().st_size
        except FileNotFoundError:
            return False
        except OSError:
            size = 0
        if size > 0:
            return True
        emit(WarningEvent(message=t("cache.invalid_entry"), file=str(source)))
        return False

    def _prepare_folder(self, folder: Path) -> None:
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise CacheError(
                t("cache.folder_unreachable"),
                file=folder,
                hint=t("cache.folder_unreachable_hint"),
            ) from error

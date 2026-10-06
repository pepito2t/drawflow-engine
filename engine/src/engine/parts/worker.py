from dataclasses import dataclass, field
from pathlib import Path

from engine.core.anomalies import Anomaly
from engine.core.cache import FileCache
from engine.core.events import Event, WarningEvent
from engine.parts.oda import OdaConverter, ensure_dxf
from engine.parts.reader import RawPart, read_parts

DXF_CACHE_NAMESPACE = "dxf"


@dataclass(frozen=True)
class FileExtraction:
    parts: list[RawPart]
    warnings: list[Anomaly] = field(default_factory=list)


def extract_file(path: Path, *, oda_executable: Path | None, cache_root: Path) -> FileExtraction:
    """Runs in a worker process: events cannot cross back, so warnings are returned instead."""
    warnings: list[Anomaly] = []

    def collect(event: Event) -> None:
        if isinstance(event, WarningEvent):
            warnings.append(Anomaly(event.message, event.location, event.hint))

    converter = OdaConverter(oda_executable or Path())
    dxf = ensure_dxf(path, FileCache(cache_root, DXF_CACHE_NAMESPACE), converter, collect)
    return FileExtraction(parts=read_parts(dxf, path, collect), warnings=warnings)

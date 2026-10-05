import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from engine.core.cache import CacheError, FileCache, file_digest, resolve_cache_root
from engine.core.events import Event, WarningEvent
from engine.core.settings_models import GeneralSettings


class CountingProducer:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def __call__(self, source: Path, target: Path) -> None:
        self.calls.append(source)
        target.write_text(source.read_text(encoding="utf-8").upper(), encoding="utf-8")


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "Plan façade é.dwg"
    path.write_text("contenu", encoding="utf-8")
    return path


def test_digest_matches_sha256(source: Path) -> None:
    assert file_digest(source) == hashlib.sha256(b"contenu").hexdigest()


def test_second_request_hits_the_cache(tmp_path: Path, source: Path) -> None:
    cache = FileCache(tmp_path / "cache", "dxf")
    producer = CountingProducer()
    events: list[Event] = []

    first = cache.get_or_create(source, ".dxf", producer, events.append)
    second = cache.get_or_create(source, ".dxf", producer, events.append)

    assert first == second
    assert first.read_text(encoding="utf-8") == "CONTENU"
    assert len(producer.calls) == 1


def test_identical_content_under_another_name_is_reused(tmp_path: Path, source: Path) -> None:
    copy = tmp_path / "copie.dwg"
    copy.write_bytes(source.read_bytes())
    cache = FileCache(tmp_path / "cache", "dxf")
    producer = CountingProducer()
    events: list[Event] = []

    cache.get_or_create(source, ".dxf", producer, events.append)
    cache.get_or_create(copy, ".dxf", producer, events.append)

    assert producer.calls == [source]


def test_empty_entry_is_recomputed_with_a_warning(tmp_path: Path, source: Path) -> None:
    cache = FileCache(tmp_path / "cache", "dxf")
    entry = cache.entry_path(file_digest(source), ".dxf")
    entry.parent.mkdir(parents=True)
    entry.write_text("", encoding="utf-8")
    producer = CountingProducer()
    events: list[Event] = []

    result = cache.get_or_create(source, ".dxf", producer, events.append)

    assert result.read_text(encoding="utf-8") == "CONTENU"
    assert isinstance(events[0], WarningEvent)


def test_failed_production_leaves_no_entry(tmp_path: Path, source: Path) -> None:
    cache = FileCache(tmp_path / "cache", "dxf")

    def failing(_: Path, __: Path) -> None:
        raise RuntimeError("conversion impossible")

    with pytest.raises(RuntimeError):
        cache.get_or_create(source, ".dxf", failing, lambda _: None)

    assert not cache.entry_path(file_digest(source), ".dxf").exists()
    assert list(cache.entry_path(file_digest(source), ".dxf").parent.iterdir()) == []


def test_parallel_productions_of_identical_files_keep_the_entry_intact(
    tmp_path: Path, source: Path
) -> None:
    cache = FileCache(tmp_path / "cache", "dxf")
    workers = 4
    expected = "CONTENU" * 50

    def slow_producer(_: Path, target: Path) -> None:
        with target.open("w", encoding="utf-8") as stream:
            for _ in range(50):
                stream.write("CONTENU")
                stream.flush()
                time.sleep(0.001)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        entries = list(
            pool.map(
                lambda _: cache.get_or_create(source, ".dxf", slow_producer, lambda _: None),
                range(workers),
            )
        )

    assert len(set(entries)) == 1
    assert entries[0].read_text(encoding="utf-8") == expected
    assert [path.name for path in entries[0].parent.iterdir()] == [entries[0].name]


def test_unwritable_cache_folder_is_reported(tmp_path: Path, source: Path) -> None:
    blocker = tmp_path / "bloqué"
    blocker.write_text("", encoding="utf-8")
    cache = FileCache(blocker, "dxf")

    with pytest.raises(CacheError) as caught:
        cache.get_or_create(source, ".dxf", CountingProducer(), lambda _: None)

    assert caught.value.hint is not None


def test_configured_cache_folder_wins(tmp_path: Path) -> None:
    assert resolve_cache_root(GeneralSettings(cache_folder=tmp_path)) == tmp_path
    assert resolve_cache_root(GeneralSettings()).name in {"drawflow", "cache"}

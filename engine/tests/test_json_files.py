import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from engine.core.json_files import TEMPORARY_SUFFIX, temporary_path, write_json_atomically


def _leftovers(folder: Path) -> list[Path]:
    return [path for path in folder.iterdir() if path.name.endswith(TEMPORARY_SUFFIX)]


def test_every_write_uses_its_own_temporary_name(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"

    first, second = temporary_path(target), temporary_path(target)

    assert first != second
    assert first.parent == target.parent and first.name.endswith(TEMPORARY_SUFFIX)


def test_concurrent_writers_leave_one_valid_file_and_no_leftover(tmp_path: Path) -> None:
    target = tmp_path / "config" / "history.json"
    payloads = [{"writer": index} for index in range(8)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda payload: write_json_atomically(target, payload), payloads))

    assert json.loads(target.read_text(encoding="utf-8")) in payloads
    assert _leftovers(target.parent) == []


def test_failed_write_keeps_the_previous_file_and_cleans_up(tmp_path: Path) -> None:
    target = tmp_path / "presets.json"
    target.write_text("[]", encoding="utf-8")

    with pytest.raises(TypeError):
        write_json_atomically(target, {"bad": object()})

    assert target.read_text(encoding="utf-8") == "[]"
    assert _leftovers(tmp_path) == []

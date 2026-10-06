import json
from pathlib import Path

from engine.core.diagnostics import MAX_LOG_BYTES, log_file, record_failure
from engine.core.errors import EngineError


def _entries(settings: Path) -> list[dict[str, object]]:
    path = log_file(settings)
    assert path is not None
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_business_error_is_logged_with_its_underlying_cause(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    try:
        raise EngineError("Le serveur a refusé.", hint="Vérifiez.", file=Path("C:/a.dwg"))
    except EngineError as error:
        error.__cause__ = RuntimeError('{"error": "model requires more system memory"}')
        record_failure(settings, ["assistant", "chat"], error)

    [entry] = _entries(settings)
    assert entry["type"] == "EngineError"
    assert entry["message"] == "Le serveur a refusé."
    assert entry["file"] == str(Path("C:/a.dwg"))
    assert "more system memory" in str(entry["cause"])
    assert entry["command"] == ["assistant", "chat"]


def test_internal_error_keeps_its_traceback(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    try:
        raise ValueError("boom")
    except ValueError as error:
        record_failure(settings, ["run", "dwg-parts"], error)

    [entry] = _entries(settings)
    assert entry["type"] == "ValueError"
    assert "Traceback" in str(entry["cause"]) and "boom" in str(entry["cause"])


def test_log_rotates_once_it_grows_too_big(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    path = log_file(settings)
    assert path is not None
    path.parent.mkdir()
    path.write_bytes(b"x" * MAX_LOG_BYTES)

    record_failure(settings, ["run"], EngineError("après rotation"))

    assert path.with_name("engine.log.1").stat().st_size == MAX_LOG_BYTES
    assert len(_entries(settings)) == 1


def test_without_settings_or_unwritable_folder_nothing_breaks(tmp_path: Path) -> None:
    record_failure(None, ["list-modules"], EngineError("x"))
    blocked = tmp_path / "file"
    blocked.write_text("", encoding="utf-8")

    record_failure(blocked / "settings.json", ["run"], EngineError("x"))
